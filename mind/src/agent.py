"""
Core Agent implementation for recursive task solving.

Each agent can decompose tasks, spawn subagents, use tools, and evaluate results.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional, Literal
from uuid import UUID, uuid4
from datetime import datetime
import anthropic
import structlog

logger = structlog.get_logger()


class Agent:
    """
    A recursive agent that can solve tasks by decomposition or direct execution.
    """

    def __init__(
        self,
        agent_id: UUID,
        task_id: UUID,
        assigned_task: str,
        context: Dict[str, Any],
        parent_id: Optional[UUID] = None,
        depth: int = 0,
        max_depth: int = 10,
        timeout_seconds: int = 300,
    ):
        self.agent_id = agent_id
        self.task_id = task_id
        self.assigned_task = assigned_task
        self.context = context
        self.parent_id = parent_id
        self.depth = depth
        self.max_depth = max_depth
        self.timeout_seconds = timeout_seconds

        # State
        self.status = "created"
        self.result = None
        self.thoughts = ""
        self.synthesis = ""
        self.learnings = []
        self.subagents: List[Agent] = []

        # Metrics
        self.started_at = None
        self.completed_at = None
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.cost_usd = 0.0

        # Claude client
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY", os.getenv("API_KEY", ""))
        )
        self.model = os.getenv("MODEL_NAME", "claude-sonnet-4-5-20250929")

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost in USD based on token usage and model pricing.

        Pricing (as of Jan 2025):
        - Claude Sonnet 4.5: $3/MTok input, $15/MTok output
        - Claude Opus 4: $15/MTok input, $75/MTok output
        - Claude Haiku 3.5: $1/MTok input, $5/MTok output
        """
        pricing = {
            "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
            "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
            "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
            "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        }

        # Get pricing for current model (default to Sonnet 4.5)
        model_pricing = pricing.get(
            self.model,
            {"input": 3.0, "output": 15.0}
        )

        # Calculate cost per million tokens
        input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (output_tokens / 1_000_000) * model_pricing["output"]

        return input_cost + output_cost

    async def solve(self) -> Dict[str, Any]:
        """
        Main recursive solving algorithm.
        
        Returns:
            Dictionary containing result, thoughts, synthesis, and learnings
        """
        self.started_at = datetime.utcnow()
        self.status = "running"

        logger.info(
            "agent_started",
            agent_id=str(self.agent_id),
            depth=self.depth,
            task=self.assigned_task[:100]
        )

        try:
            # 1. Analyze task and decide approach
            decision = await self._decide_approach()

            if decision["approach"] == "direct":
                # 2a. Solve directly using tools
                result = await self._solve_directly()
            else:
                # 2b. Decompose and spawn subagents
                result = await self._solve_recursively(decision["subtasks"])

            self.result = result
            self.status = "completed"
            self.completed_at = datetime.utcnow()

            logger.info(
                "agent_completed",
                agent_id=str(self.agent_id),
                status="success"
            )

            return {
                "result": self.result,
                "thoughts": self.thoughts,
                "synthesis": self.synthesis,
                "learnings": self.learnings
            }

        except Exception as e:
            self.status = "failed"
            self.completed_at = datetime.utcnow()

            logger.error(
                "agent_failed",
                agent_id=str(self.agent_id),
                error=str(e)
            )

            raise

    async def _decide_approach(self) -> Dict[str, Any]:
        """
        Decide whether to solve directly or decompose into subtasks.
        """
        # Check if we've hit recursion limit
        if self.depth >= self.max_depth:
            return {"approach": "direct"}

        # Ask Claude to analyze and decide
        prompt = f"""You are an AGI agent analyzing a task to determine the best approach.

Task: {self.assigned_task}

Context:
{self.context}

Current depth: {self.depth}/{self.max_depth}

Decide:
1. Can this task be solved DIRECTLY using available tools? (web_search, db_query, execute_code, store_data)
2. Or should it be DECOMPOSED into smaller subtasks?

If DIRECT, respond with: {{"approach": "direct", "reasoning": "why"}}
If DECOMPOSE, respond with: {{"approach": "decompose", "subtasks": ["task1", "task2", ...], "reasoning": "why"}}

Be concise. Only decompose if the task is genuinely complex."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        self.prompt_tokens += response.usage.input_tokens
        self.completion_tokens += response.usage.output_tokens
        self.cost_usd += self._calculate_cost(
            response.usage.input_tokens,
            response.usage.output_tokens
        )

        # Parse response (simplified - in production use structured output)
        content = response.content[0].text
        
        # Simple parsing logic
        if "\"approach\": \"direct\"" in content or self.depth >= self.max_depth - 1:
            return {"approach": "direct"}
        else:
            # Extract subtasks (simplified)
            return {
                "approach": "decompose",
                "subtasks": self._parse_subtasks(content)
            }

    def _parse_subtasks(self, content: str) -> List[str]:
        """Parse subtasks from Claude's response."""
        # Simplified parsing - in production use JSON parsing
        import re
        match = re.search(r'"subtasks":\s*\[(.*?)\]', content, re.DOTALL)
        if match:
            tasks_str = match.group(1)
            tasks = re.findall(r'"([^"]+)"', tasks_str)
            return tasks[:5]  # Limit to 5 subtasks
        return [self.assigned_task]  # Fallback

    async def _solve_directly(self) -> Dict[str, Any]:
        """
        Solve task directly using available tools.
        """
        # Build tool definitions for Claude
        tools = self._get_tool_definitions()

        messages = [{
            "role": "user",
            "content": f"""Solve this task using available tools:

Task: {self.assigned_task}

Context: {self.context}

Use tools as needed and provide a final answer."""
        }]

        # Agentic loop with tool use
        max_iterations = 10
        for iteration in range(max_iterations):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                tools=tools,
                messages=messages
            )

            self.prompt_tokens += response.usage.input_tokens
            self.completion_tokens += response.usage.output_tokens
            self.cost_usd += self._calculate_cost(
                response.usage.input_tokens,
                response.usage.output_tokens
            )

            # Check if we're done
            if response.stop_reason == "end_turn":
                # Extract final answer
                final_text = ""
                for block in response.content:
                    if block.type == "text":
                        final_text += block.text

                self.thoughts = final_text
                return {"answer": final_text, "success": True}

            # Process tool calls
            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await self._execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result)
                        })

                # Add to messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                break

        return {"answer": "Task completed", "success": True}

    async def _solve_recursively(self, subtasks: List[str]) -> Dict[str, Any]:
        """
        Solve by decomposing into subtasks and spawning subagents.
        """
        logger.info(
            "decomposing_task",
            agent_id=str(self.agent_id),
            num_subtasks=len(subtasks)
        )

        subagent_results = []

        for idx, subtask in enumerate(subtasks):
            # Spawn subagent
            subagent = Agent(
                agent_id=uuid4(),
                task_id=self.task_id,
                assigned_task=subtask,
                context=self.context,
                parent_id=self.agent_id,
                depth=self.depth + 1,
                max_depth=self.max_depth,
                timeout_seconds=self.timeout_seconds
            )

            self.subagents.append(subagent)

            # Execute subagent
            subagent_result = await subagent.solve()

            # Evaluate result
            evaluation = await self._evaluate_subagent_result(
                subtask, subagent_result
            )

            if evaluation["decision"] == "accept":
                subagent_results.append(subagent_result)
            elif evaluation["decision"] == "revise":
                # Request revision (simplified - just log for now)
                logger.info(
                    "revision_requested",
                    subagent_id=str(subagent.agent_id),
                    feedback=evaluation["feedback"]
                )
                subagent_results.append(subagent_result)  # Accept anyway for now
            else:
                # Reject
                logger.warning(
                    "subagent_rejected",
                    subagent_id=str(subagent.agent_id)
                )

        # Synthesize results
        synthesized = await self._synthesize_results(subtasks, subagent_results)

        return synthesized

    async def _evaluate_subagent_result(
        self, subtask: str, result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate a subagent's result (accept/reject/revise).
        """
        prompt = f"""Evaluate this subagent's work:

Subtask: {subtask}
Result: {result}

Decide: accept, reject, or revise?
Provide reasoning and feedback if needed.

Respond with JSON: {{"decision": "accept/reject/revise", "score": 0.0-1.0, "reasoning": "...", "feedback": "..."}}"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        self.prompt_tokens += response.usage.input_tokens
        self.completion_tokens += response.usage.output_tokens
        self.cost_usd += self._calculate_cost(
            response.usage.input_tokens,
            response.usage.output_tokens
        )

        content = response.content[0].text

        # Simple parsing
        if "accept" in content.lower():
            return {"decision": "accept", "score": 0.8}
        elif "reject" in content.lower():
            return {"decision": "reject", "score": 0.3}
        else:
            return {"decision": "revise", "score": 0.6, "feedback": "Please improve"}

    async def _synthesize_results(
        self, subtasks: List[str], results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesize subagent results into a final answer.
        """
        prompt = f"""Synthesize these subagent results into a final answer:

Original task: {self.assigned_task}

Subtasks and results:
"""
        for subtask, result in zip(subtasks, results):
            prompt += f"\n- {subtask}: {result.get('result', result)}"

        prompt += "\n\nProvide a synthesized final answer with key insights:"

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        self.prompt_tokens += response.usage.input_tokens
        self.completion_tokens += response.usage.output_tokens
        self.cost_usd += self._calculate_cost(
            response.usage.input_tokens,
            response.usage.output_tokens
        )

        synthesis = response.content[0].text
        self.synthesis = synthesis

        return {
            "answer": synthesis,
            "subagent_results": results,
            "success": True
        }

    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Define available tools for Claude."""
        return [
            {
                "name": "web_search",
                "description": "Search the internet for information",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "num_results": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "db_query",
                "description": "Query the knowledge database",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "category": {"type": "string", "description": "Category filter"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "execute_code",
                "description": "Execute code in a sandbox",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to execute"},
                        "language": {"type": "string", "default": "python"}
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "store_data",
                "description": "Store data in the knowledge base",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "object", "description": "Data to store"},
                        "category": {"type": "string", "description": "Category"},
                        "summary": {"type": "string", "description": "Brief summary"}
                    },
                    "required": ["data", "category"]
                }
            }
        ]

    async def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """
        Execute a tool call.
        """
        logger.info("tool_called", tool=tool_name, agent_id=str(self.agent_id))

        # Tool implementations (placeholders)
        if tool_name == "web_search":
            return f"Search results for: {tool_input.get('query')}"
        elif tool_name == "db_query":
            return []
        elif tool_name == "execute_code":
            return {"stdout": "Code executed successfully", "exit_code": 0}
        elif tool_name == "store_data":
            return {"success": True, "stored_id": str(uuid4())}
        else:
            return {"error": "Unknown tool"}
