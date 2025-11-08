"""
Anthropic API client wrapper with streaming and tool calling support.
"""
from typing import List, Dict, Any, Optional, Iterator, Union
from anthropic import Anthropic
from anthropic.types import Message, MessageStreamEvent
import json


class AnthropicClient:
    """Wrapper for Anthropic API with convenience methods."""

    def __init__(self, api_key: str, default_model: str = "claude-sonnet-4-5-20250929"):
        """Initialize the Anthropic client.

        Args:
            api_key: Anthropic API key
            default_model: Default model to use for completions
        """
        self.client = Anthropic(api_key=api_key)
        self.default_model = default_model

    def create_message(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Message:
        """Create a message using the Anthropic API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: Optional system prompt
            model: Model to use (defaults to default_model)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            tools: Optional list of tool definitions

        Returns:
            Message response from the API
        """
        params = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system:
            params["system"] = system

        if tools:
            params["tools"] = tools

        return self.client.messages.create(**params)

    def create_message_stream(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Iterator[MessageStreamEvent]:
        """Create a streaming message using the Anthropic API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: Optional system prompt
            model: Model to use (defaults to default_model)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            tools: Optional list of tool definitions

        Yields:
            Stream events from the API
        """
        params = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system:
            params["system"] = system

        if tools:
            params["tools"] = tools

        with self.client.messages.stream(**params) as stream:
            for event in stream:
                yield event

    def extract_text_from_message(self, message: Message) -> str:
        """Extract text content from a message response.

        Args:
            message: Message response from the API

        Returns:
            Extracted text content
        """
        text_parts = []
        for block in message.content:
            if block.type == "text":
                text_parts.append(block.text)
        return "".join(text_parts)

    def extract_tool_calls_from_message(self, message: Message) -> List[Dict[str, Any]]:
        """Extract tool use blocks from a message response.

        Args:
            message: Message response from the API

        Returns:
            List of tool call dicts with 'id', 'name', and 'input'
        """
        tool_calls = []
        for block in message.content:
            if block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
        return tool_calls

    def format_tool_result(self, tool_use_id: str, result: Any) -> Dict[str, Any]:
        """Format a tool result for inclusion in messages.

        Args:
            tool_use_id: ID of the tool use block
            result: Result from tool execution

        Returns:
            Formatted tool result dict
        """
        # Convert result to string if not already
        if not isinstance(result, str):
            result = json.dumps(result)

        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": result,
        }
