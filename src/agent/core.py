"""
Core AGI agent with memory integration and tool execution.
"""
from typing import List, Dict, Any, Optional, Iterator
from dataclasses import dataclass
from datetime import datetime
import json

from ..api.client import AnthropicClient
from ..memory.store import MemoryStore
from .tools import ToolRegistry


@dataclass
class AgentResponse:
    """Response from the AGI agent."""
    content: str
    tool_calls: List[Dict[str, Any]]
    memories_used: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class AGIAgent:
    """Core AGI agent with memory and tool execution capabilities."""

    def __init__(
        self,
        api_client: AnthropicClient,
        memory_store: MemoryStore,
        tool_registry: ToolRegistry,
        system_prompt: Optional[str] = None,
        max_memory_results: int = 5,
        memory_relevance_threshold: float = 0.7,
        max_tool_iterations: int = 5,
    ):
        """Initialize the AGI agent.

        Args:
            api_client: Anthropic API client
            memory_store: Memory storage instance
            tool_registry: Tool registry instance
            system_prompt: Optional system prompt
            max_memory_results: Maximum number of memories to retrieve
            memory_relevance_threshold: Minimum relevance score for memories
            max_tool_iterations: Maximum number of tool execution iterations
        """
        self.api_client = api_client
        self.memory_store = memory_store
        self.tool_registry = tool_registry
        self.max_memory_results = max_memory_results
        self.memory_relevance_threshold = memory_relevance_threshold
        self.max_tool_iterations = max_tool_iterations

        # Build system prompt
        self.system_prompt = system_prompt or self._build_default_system_prompt()

    def _build_default_system_prompt(self) -> str:
        """Build the default system prompt for the agent.

        Returns:
            System prompt string
        """
        return """You are an advanced AGI assistant with access to long-term memory and various tools.

You have the following capabilities:
1. **Long-term Memory**: You can remember information across conversations. Important facts, user preferences, and context are stored in your memory system.
2. **Tool Execution**: You can call various tools to perform actions, retrieve information, or interact with external systems.

When interacting with users:
- Use your memory to provide personalized and contextual responses
- Store important information in memory for future reference
- Use available tools when they can help accomplish the user's goals
- Be transparent about what you remember and what tools you're using

You are helpful, harmless, and honest. You aim to be a capable and reliable assistant."""

    def _retrieve_relevant_memories(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for a query.

        Args:
            query: Search query

        Returns:
            List of relevant memories
        """
        memories = self.memory_store.search_memories(
            query=query,
            n_results=self.max_memory_results,
        )

        # Filter by relevance threshold
        relevant_memories = [
            m for m in memories
            if m.get("relevance", 0) >= self.memory_relevance_threshold
        ]

        return relevant_memories

    def _format_memories_for_context(self, memories: List[Dict[str, Any]]) -> str:
        """Format memories for inclusion in the prompt.

        Args:
            memories: List of memory dicts

        Returns:
            Formatted memory context string
        """
        if not memories:
            return ""

        memory_texts = []
        for mem in memories:
            timestamp = mem.get("metadata", {}).get("timestamp", "unknown")
            content = mem.get("content", "")
            relevance = mem.get("relevance", 0)
            memory_texts.append(
                f"[Memory from {timestamp}, relevance: {relevance:.2f}]\n{content}"
            )

        return "\n\n".join(memory_texts)

    def process_message(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        store_in_memory: bool = True,
    ) -> AgentResponse:
        """Process a user message and generate a response.

        Args:
            user_message: The user's message
            conversation_history: Optional conversation history
            store_in_memory: Whether to store the interaction in memory

        Returns:
            AgentResponse with content and metadata
        """
        # Retrieve relevant memories
        memories = self._retrieve_relevant_memories(user_message)

        # Build the conversation context
        messages = conversation_history or []

        # Add memory context to the user message if memories exist
        enhanced_message = user_message
        if memories:
            memory_context = self._format_memories_for_context(memories)
            enhanced_message = f"""Relevant memories:
{memory_context}

User message:
{user_message}"""

        # Add current message
        messages.append({
            "role": "user",
            "content": enhanced_message,
        })

        # Get tool definitions
        tool_definitions = self.tool_registry.get_tool_definitions()

        # Execute conversation with tool calling loop
        iterations = 0
        all_tool_calls = []

        while iterations < self.max_tool_iterations:
            # Call the API
            response = self.api_client.create_message(
                messages=messages,
                system=self.system_prompt,
                tools=tool_definitions if tool_definitions else None,
            )

            # Extract response content
            text_content = self.api_client.extract_text_from_message(response)
            tool_calls = self.api_client.extract_tool_calls_from_message(response)

            # If no tool calls, we're done
            if not tool_calls:
                # Store interaction in memory if requested
                if store_in_memory:
                    self._store_interaction_in_memory(user_message, text_content)

                return AgentResponse(
                    content=text_content,
                    tool_calls=all_tool_calls,
                    memories_used=memories,
                    metadata={
                        "iterations": iterations + 1,
                        "stop_reason": response.stop_reason,
                    }
                )

            # Execute tool calls
            messages.append({
                "role": "assistant",
                "content": response.content,
            })

            tool_results = []
            for tool_call in tool_calls:
                all_tool_calls.append(tool_call)

                try:
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

            # Add tool results to messages
            messages.append({
                "role": "user",
                "content": tool_results,
            })

            iterations += 1

        # Max iterations reached
        return AgentResponse(
            content="Maximum tool iterations reached.",
            tool_calls=all_tool_calls,
            memories_used=memories,
            metadata={
                "iterations": iterations,
                "stop_reason": "max_iterations",
            }
        )

    def _store_interaction_in_memory(self, user_message: str, agent_response: str):
        """Store an interaction in memory.

        Args:
            user_message: The user's message
            agent_response: The agent's response
        """
        # Store user message
        self.memory_store.add_memory(
            content=f"User said: {user_message}",
            metadata={
                "type": "user_message",
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Store agent response
        self.memory_store.add_memory(
            content=f"Assistant responded: {agent_response}",
            metadata={
                "type": "assistant_response",
                "timestamp": datetime.now().isoformat(),
            }
        )

    def add_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Manually add a memory.

        Args:
            content: Memory content
            metadata: Optional metadata

        Returns:
            Memory ID
        """
        return self.memory_store.add_memory(content=content, metadata=metadata)

    def search_memories(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search memories.

        Args:
            query: Search query
            n_results: Number of results

        Returns:
            List of relevant memories
        """
        return self.memory_store.search_memories(query=query, n_results=n_results)
