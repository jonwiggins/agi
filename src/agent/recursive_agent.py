"""
Recursive sub-agent architecture for complex task decomposition.

This module implements a recursive agent system where:
1. A parent agent receives a complex task
2. It breaks down the task into subtasks
3. Spawns sub-agents to handle each subtask
4. Evaluates sub-agent results (accept/reject with feedback)
5. Synthesizes results back up the chain
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid

from ..api.client import AnthropicClient
from ..memory.store import MemoryStore
from .enhanced_tools import EnhancedToolRegistry


class AgentStatus(str, Enum):
    """Status of an agent's execution."""
    PENDING = "pending"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING_FOR_SUBAGENTS = "waiting_for_subagents"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationResult(str, Enum):
    """Result of evaluating a sub-agent's output."""
    ACCEPT = "accept"
    REJECT = "reject"
    NEEDS_REFINEMENT = "needs_refinement"


@dataclass
class AgentContext:
    """Context passed to agents containing task and parent information."""
    agent_id: str
    task: str
    parent_context: Optional[str] = None
    overall_goal: str = ""
    depth: int = 0
    max_depth: int = 5
    parent_agent_id: Optional[str] = None
    constraints: List[str] = field(default_factory=list)
    available_tools: List[str] = field(default_factory=list)


@dataclass
class SubAgentRequest:
    """Request to create a sub-agent."""
    subtask: str
    context: str
    expected_output: str
    constraints: List[str] = field(default_factory=list)


@dataclass
class SubAgentResult:
    """Result from a sub-agent's execution."""
    agent_id: str
    subtask: str
    output: str
    thoughts: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    status: AgentStatus = AgentStatus.COMPLETED
    error: Optional[str] = None


@dataclass
class EvaluationFeedback:
    """Feedback from evaluating a result."""
    result: EvaluationResult
    reasoning: str
    suggested_changes: List[str] = field(default_factory=list)
    additional_context: str = ""


@dataclass
class AgentThought:
    """A thought/reasoning step from the agent."""
    timestamp: str
    thought: str
    thought_type: str  # "analysis", "planning", "evaluation", "synthesis"


class RecursiveAgent:
    """
    A recursive agent that can spawn sub-agents to solve complex tasks.

    Features:
    - Task decomposition
    - Sub-agent spawning
    - Result evaluation and validation
    - Iterative refinement
    - Context propagation
    """

    def __init__(
        self,
        api_client: AnthropicClient,
        memory_store: MemoryStore,
        tool_registry: EnhancedToolRegistry,
        max_depth: int = 5,
        max_iterations: int = 3,
        max_subagents: int = 5,
    ):
        """Initialize the recursive agent.

        Args:
            api_client: Anthropic API client
            memory_store: Memory storage
            tool_registry: Enhanced tool registry
            max_depth: Maximum recursion depth
            max_iterations: Maximum refinement iterations per subtask
            max_subagents: Maximum sub-agents per parent
        """
        self.api_client = api_client
        self.memory_store = memory_store
        self.tool_registry = tool_registry
        self.max_depth = max_depth
        self.max_iterations = max_iterations
        self.max_subagents = max_subagents

        # Track all agents in the execution tree
        self.agent_tree: Dict[str, Dict[str, Any]] = {}
        self.thoughts: Dict[str, List[AgentThought]] = {}

    def execute_task(
        self,
        task: str,
        context: Optional[AgentContext] = None,
    ) -> SubAgentResult:
        """Execute a task, potentially spawning sub-agents.

        Args:
            task: The task to execute
            context: Agent context (created if None)

        Returns:
            Result of the task execution
        """
        # Create context if not provided
        if context is None:
            context = AgentContext(
                agent_id=str(uuid.uuid4()),
                task=task,
                overall_goal=task,
                depth=0,
                max_depth=self.max_depth,
                available_tools=self.tool_registry.list_tools(),
            )

        # Register this agent in the tree
        self.agent_tree[context.agent_id] = {
            "task": task,
            "depth": context.depth,
            "parent_id": context.parent_agent_id,
            "status": AgentStatus.PENDING,
            "children": [],
        }
        self.thoughts[context.agent_id] = []

        # Check depth limit
        if context.depth >= self.max_depth:
            self._add_thought(
                context.agent_id,
                f"Reached maximum depth ({self.max_depth}), executing directly",
                "analysis"
            )
            return self._execute_direct(context)

        # Phase 1: Ultra-think (analyze and plan)
        self._update_status(context.agent_id, AgentStatus.THINKING)
        analysis = self._ultra_think(context)

        # Phase 2: Decide if decomposition is needed
        if analysis["needs_decomposition"]:
            self._add_thought(
                context.agent_id,
                f"Task requires decomposition into {len(analysis['subtasks'])} subtasks",
                "planning"
            )
            return self._execute_with_subagents(context, analysis)
        else:
            self._add_thought(
                context.agent_id,
                "Task can be executed directly without decomposition",
                "planning"
            )
            return self._execute_direct(context)

    def _ultra_think(self, context: AgentContext) -> Dict[str, Any]:
        """
        Deep thinking/reasoning phase to analyze the task.

        Uses Claude to:
        1. Analyze the task complexity
        2. Identify subtasks if decomposition needed
        3. Plan the execution strategy
        4. Identify potential issues

        Args:
            context: Agent context

        Returns:
            Analysis with decomposition decision and plan
        """
        system_prompt = """You are an expert task analyzer and planner. Your role is to:
1. Deeply analyze the given task
2. Determine if it needs to be broken down into subtasks
3. If so, identify clear, actionable subtasks
4. Consider potential issues and dependencies

Respond in JSON format with:
{
    "analysis": "Deep analysis of the task",
    "needs_decomposition": true/false,
    "reasoning": "Why decomposition is/isn't needed",
    "subtasks": [
        {
            "description": "Subtask description",
            "rationale": "Why this subtask is needed",
            "expected_output": "What output is expected",
            "dependencies": ["other subtask indices if any"]
        }
    ],
    "potential_issues": ["issue1", "issue2"],
    "recommended_tools": ["tool1", "tool2"]
}"""

        user_prompt = f"""Task: {context.task}

Overall Goal: {context.overall_goal}
Current Depth: {context.depth}/{context.max_depth}
Parent Context: {context.parent_context or 'None (top-level task)'}

Available Tools: {', '.join(context.available_tools)}

Analyze this task and determine the best execution strategy."""

        messages = [{"role": "user", "content": user_prompt}]

        response = self.api_client.create_message(
            messages=messages,
            system=system_prompt,
            temperature=0.7,
        )

        response_text = self.api_client.extract_text_from_message(response)

        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text

            analysis = json.loads(json_str)

            self._add_thought(
                context.agent_id,
                f"Analysis: {analysis.get('analysis', 'N/A')}",
                "analysis"
            )

            return analysis
        except json.JSONDecodeError as e:
            self._add_thought(
                context.agent_id,
                f"Failed to parse analysis, executing directly. Error: {e}",
                "analysis"
            )
            return {
                "analysis": response_text,
                "needs_decomposition": False,
                "reasoning": "Failed to parse structured response",
                "subtasks": [],
                "potential_issues": [],
                "recommended_tools": []
            }

    def _execute_with_subagents(
        self,
        context: AgentContext,
        analysis: Dict[str, Any]
    ) -> SubAgentResult:
        """Execute task by spawning and managing sub-agents.

        Args:
            context: Agent context
            analysis: Analysis from ultra_think

        Returns:
            Synthesized result from all sub-agents
        """
        self._update_status(context.agent_id, AgentStatus.WAITING_FOR_SUBAGENTS)

        subtasks = analysis.get("subtasks", [])[:self.max_subagents]
        subagent_results: List[Tuple[SubAgentRequest, SubAgentResult]] = []

        # Spawn and execute sub-agents
        for i, subtask_info in enumerate(subtasks):
            self._add_thought(
                context.agent_id,
                f"Spawning sub-agent {i+1}/{len(subtasks)} for: {subtask_info['description']}",
                "planning"
            )

            # Create sub-agent context
            sub_context = AgentContext(
                agent_id=str(uuid.uuid4()),
                task=subtask_info["description"],
                parent_context=context.task,
                overall_goal=context.overall_goal,
                depth=context.depth + 1,
                max_depth=context.max_depth,
                parent_agent_id=context.agent_id,
                available_tools=context.available_tools,
            )

            # Track child relationship
            self.agent_tree[context.agent_id]["children"].append(sub_context.agent_id)

            # Execute sub-agent with evaluation loop
            sub_result = self._execute_with_evaluation_loop(sub_context, subtask_info)

            subagent_results.append((
                SubAgentRequest(
                    subtask=subtask_info["description"],
                    context=context.task,
                    expected_output=subtask_info.get("expected_output", ""),
                ),
                sub_result
            ))

        # Synthesize results
        self._update_status(context.agent_id, AgentStatus.EVALUATING)
        return self._synthesize_results(context, subagent_results, analysis)

    def _execute_with_evaluation_loop(
        self,
        context: AgentContext,
        subtask_info: Dict[str, Any]
    ) -> SubAgentResult:
        """Execute a sub-agent with evaluation and refinement loop.

        Args:
            context: Sub-agent context
            subtask_info: Information about the subtask

        Returns:
            Accepted result after potential refinement iterations
        """
        for iteration in range(self.max_iterations):
            self._add_thought(
                context.agent_id,
                f"Attempt {iteration + 1}/{self.max_iterations}",
                "execution"
            )

            # Execute the subtask
            result = self._execute_direct(context)

            # Evaluate the result
            evaluation = self._evaluate_result(
                result,
                subtask_info.get("expected_output", ""),
                context
            )

            self._add_thought(
                context.agent_id,
                f"Evaluation: {evaluation.result.value} - {evaluation.reasoning}",
                "evaluation"
            )

            if evaluation.result == EvaluationResult.ACCEPT:
                # Add evaluation thoughts to result
                result.thoughts += f"\n\n[Accepted after {iteration + 1} iteration(s)]"
                return result

            elif evaluation.result == EvaluationResult.REJECT:
                if iteration < self.max_iterations - 1:
                    # Provide feedback for refinement
                    context.constraints.extend(evaluation.suggested_changes)
                    self._add_thought(
                        context.agent_id,
                        f"Refinement needed: {', '.join(evaluation.suggested_changes)}",
                        "evaluation"
                    )
                else:
                    # Max iterations reached, return with failure note
                    result.status = AgentStatus.FAILED
                    result.error = f"Failed evaluation after {self.max_iterations} attempts"
                    return result

        # Should not reach here, but return last result
        return result

    def _execute_direct(self, context: AgentContext) -> SubAgentResult:
        """Execute a task directly using available tools.

        Args:
            context: Agent context

        Returns:
            Result of direct execution
        """
        self._update_status(context.agent_id, AgentStatus.EXECUTING)

        system_prompt = f"""You are an AI agent executing a specific task. You have access to tools to help you.

Overall Goal: {context.overall_goal}
Your Specific Task: {context.task}
{f'Parent Context: {context.parent_context}' if context.parent_context else ''}
Depth: {context.depth}/{context.max_depth}

{f'Constraints: {", ".join(context.constraints)}' if context.constraints else ''}

Execute the task using available tools as needed. Provide:
1. Your reasoning and approach
2. The solution/output
3. Any important notes or caveats"""

        messages = [{"role": "user", "content": f"Execute this task: {context.task}"}]

        tool_definitions = self.tool_registry.get_tool_definitions()
        tool_calls_made = []

        # Tool execution loop
        for _ in range(10):  # Max 10 tool iterations
            response = self.api_client.create_message(
                messages=messages,
                system=system_prompt,
                tools=tool_definitions if tool_definitions else None,
            )

            text_content = self.api_client.extract_text_from_message(response)
            tool_calls = self.api_client.extract_tool_calls_from_message(response)

            if not tool_calls:
                # No more tools needed, we have the final answer
                self._update_status(context.agent_id, AgentStatus.COMPLETED)
                return SubAgentResult(
                    agent_id=context.agent_id,
                    subtask=context.task,
                    output=text_content,
                    thoughts=self._get_thoughts_summary(context.agent_id),
                    tool_calls=tool_calls_made,
                    status=AgentStatus.COMPLETED,
                )

            # Execute tools
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []

            for tool_call in tool_calls:
                tool_calls_made.append(tool_call)

                try:
                    # Special handling for create_subagent tool
                    if tool_call["name"] == "create_subagent":
                        result = self._handle_subagent_creation(tool_call, context)
                    else:
                        result = self.tool_registry.execute_tool(
                            name=tool_call["name"],
                            arguments=tool_call["input"],
                        )

                    tool_result = self.api_client.format_tool_result(
                        tool_use_id=tool_call["id"],
                        result=result,
                    )
                except Exception as e:
                    tool_result = self.api_client.format_tool_result(
                        tool_use_id=tool_call["id"],
                        result={"error": str(e)},
                    )

                tool_results.append(tool_result)

            messages.append({"role": "user", "content": tool_results})

        # Max iterations reached
        self._update_status(context.agent_id, AgentStatus.COMPLETED)
        return SubAgentResult(
            agent_id=context.agent_id,
            subtask=context.task,
            output=text_content or "Task completed with tool iterations limit reached",
            thoughts=self._get_thoughts_summary(context.agent_id),
            tool_calls=tool_calls_made,
            status=AgentStatus.COMPLETED,
        )

    def _handle_subagent_creation(
        self,
        tool_call: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle the create_subagent tool call recursively.

        Args:
            tool_call: Tool call data
            context: Current agent context

        Returns:
            Sub-agent execution result
        """
        arguments = tool_call["input"]
        subtask = arguments.get("subtask", "")
        subtask_context = arguments.get("context", "")
        expected_output = arguments.get("expected_output", "")

        # Create sub-agent context
        sub_context = AgentContext(
            agent_id=str(uuid.uuid4()),
            task=subtask,
            parent_context=f"{context.task}\n\nAdditional context: {subtask_context}",
            overall_goal=context.overall_goal,
            depth=context.depth + 1,
            max_depth=context.max_depth,
            parent_agent_id=context.agent_id,
            available_tools=context.available_tools,
        )

        # Track relationship
        if context.agent_id in self.agent_tree:
            self.agent_tree[context.agent_id]["children"].append(sub_context.agent_id)

        # Execute recursively
        result = self.execute_task(subtask, sub_context)

        return {
            "subagent_id": result.agent_id,
            "output": result.output,
            "status": result.status.value,
            "thoughts": result.thoughts,
        }

    def _evaluate_result(
        self,
        result: SubAgentResult,
        expected_output: str,
        context: AgentContext
    ) -> EvaluationFeedback:
        """Evaluate a sub-agent's result.

        Args:
            result: Sub-agent result to evaluate
            expected_output: Expected output description
            context: Agent context

        Returns:
            Evaluation feedback
        """
        system_prompt = """You are an expert evaluator of AI agent outputs. Evaluate the result objectively.

Provide evaluation in JSON format:
{
    "result": "accept" | "reject" | "needs_refinement",
    "reasoning": "Detailed reasoning for the evaluation",
    "suggested_changes": ["change1", "change2"],
    "additional_context": "Any additional context for refinement"
}"""

        user_prompt = f"""Evaluate this result:

Task: {context.task}
Expected Output: {expected_output}

Result:
{result.output}

Thoughts/Reasoning:
{result.thoughts}

Is this result acceptable?"""

        messages = [{"role": "user", "content": user_prompt}]

        response = self.api_client.create_message(
            messages=messages,
            system=system_prompt,
            temperature=0.3,  # Lower temperature for more consistent evaluation
        )

        response_text = self.api_client.extract_text_from_message(response)

        try:
            # Extract JSON
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text

            eval_data = json.loads(json_str)

            return EvaluationFeedback(
                result=EvaluationResult(eval_data.get("result", "accept")),
                reasoning=eval_data.get("reasoning", ""),
                suggested_changes=eval_data.get("suggested_changes", []),
                additional_context=eval_data.get("additional_context", ""),
            )
        except (json.JSONDecodeError, ValueError):
            # Default to accept if parsing fails
            return EvaluationFeedback(
                result=EvaluationResult.ACCEPT,
                reasoning="Evaluation parsing failed, accepting by default",
                suggested_changes=[],
            )

    def _synthesize_results(
        self,
        context: AgentContext,
        subagent_results: List[Tuple[SubAgentRequest, SubAgentResult]],
        analysis: Dict[str, Any]
    ) -> SubAgentResult:
        """Synthesize results from multiple sub-agents.

        Args:
            context: Parent agent context
            subagent_results: Results from all sub-agents
            analysis: Original task analysis

        Returns:
            Synthesized final result
        """
        system_prompt = """You are synthesizing results from multiple sub-agents into a coherent final answer.

Consider:
1. How the subtask results fit together
2. The overall goal
3. Any dependencies or relationships between subtasks
4. Potential issues or gaps

Provide a comprehensive synthesis that addresses the original task."""

        # Build synthesis prompt
        results_text = "\n\n".join([
            f"Subtask: {req.subtask}\nExpected: {req.expected_output}\nResult: {res.output}\nThoughts: {res.thoughts}"
            for req, res in subagent_results
        ])

        user_prompt = f"""Original Task: {context.task}
Overall Goal: {context.overall_goal}

Analysis: {analysis.get('analysis', 'N/A')}

Sub-agent Results:
{results_text}

Synthesize these results into a final answer for the original task."""

        messages = [{"role": "user", "content": user_prompt}]

        response = self.api_client.create_message(
            messages=messages,
            system=system_prompt,
            temperature=0.7,
        )

        synthesis = self.api_client.extract_text_from_message(response)

        # Collect all tool calls from sub-agents
        all_tool_calls = []
        for _, result in subagent_results:
            all_tool_calls.extend(result.tool_calls)

        self._update_status(context.agent_id, AgentStatus.COMPLETED)

        return SubAgentResult(
            agent_id=context.agent_id,
            subtask=context.task,
            output=synthesis,
            thoughts=self._get_thoughts_summary(context.agent_id),
            tool_calls=all_tool_calls,
            status=AgentStatus.COMPLETED,
        )

    def _add_thought(self, agent_id: str, thought: str, thought_type: str):
        """Add a thought to the agent's thought log.

        Args:
            agent_id: Agent ID
            thought: Thought text
            thought_type: Type of thought
        """
        if agent_id not in self.thoughts:
            self.thoughts[agent_id] = []

        self.thoughts[agent_id].append(AgentThought(
            timestamp=datetime.now().isoformat(),
            thought=thought,
            thought_type=thought_type,
        ))

    def _get_thoughts_summary(self, agent_id: str) -> str:
        """Get a summary of all thoughts for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Formatted thoughts summary
        """
        if agent_id not in self.thoughts:
            return ""

        thoughts = self.thoughts[agent_id]
        return "\n".join([
            f"[{t.thought_type.upper()}] {t.thought}"
            for t in thoughts
        ])

    def _update_status(self, agent_id: str, status: AgentStatus):
        """Update agent status.

        Args:
            agent_id: Agent ID
            status: New status
        """
        if agent_id in self.agent_tree:
            self.agent_tree[agent_id]["status"] = status

    def get_execution_tree(self) -> Dict[str, Any]:
        """Get the complete execution tree.

        Returns:
            Tree structure with all agents
        """
        return self.agent_tree

    def get_agent_thoughts(self, agent_id: str) -> List[AgentThought]:
        """Get thoughts for a specific agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of thoughts
        """
        return self.thoughts.get(agent_id, [])
