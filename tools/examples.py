"""
Example tools that can be registered with the AGI agent.

This module demonstrates how to create custom tools for the agent.
"""
from datetime import datetime
import json
import os
from typing import Dict, Any

from src.agent.tools import Tool, ToolParameter, ToolParameterType


def create_example_tools() -> list[Tool]:
    """Create a list of example tools.

    Returns:
        List of example Tool instances
    """
    tools = []

    # Calculator tool
    def calculator(operation: str, a: float, b: float) -> dict:
        """Perform basic arithmetic operations."""
        operations = {
            "add": lambda x, y: x + y,
            "subtract": lambda x, y: x - y,
            "multiply": lambda x, y: x * y,
            "divide": lambda x, y: x / y if y != 0 else "Error: Division by zero",
        }

        if operation not in operations:
            return {"error": f"Unknown operation: {operation}"}

        result = operations[operation](a, b)
        return {
            "operation": operation,
            "a": a,
            "b": b,
            "result": result,
        }

    tools.append(Tool(
        name="calculator",
        description="Perform basic arithmetic operations (add, subtract, multiply, divide)",
        parameters=[
            ToolParameter(
                name="operation",
                type=ToolParameterType.STRING,
                description="The operation to perform",
                required=True,
                enum=["add", "subtract", "multiply", "divide"],
            ),
            ToolParameter(
                name="a",
                type=ToolParameterType.NUMBER,
                description="First number",
                required=True,
            ),
            ToolParameter(
                name="b",
                type=ToolParameterType.NUMBER,
                description="Second number",
                required=True,
            ),
        ],
        function=calculator,
    ))

    # Get current time tool
    def get_current_time(timezone: str = "UTC") -> dict:
        """Get the current time."""
        now = datetime.now()
        return {
            "timestamp": now.isoformat(),
            "timezone": timezone,
            "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
            "unix_timestamp": int(now.timestamp()),
        }

    tools.append(Tool(
        name="get_current_time",
        description="Get the current date and time",
        parameters=[
            ToolParameter(
                name="timezone",
                type=ToolParameterType.STRING,
                description="Timezone (currently only UTC is supported)",
                required=False,
            ),
        ],
        function=get_current_time,
    ))

    # File reader tool (careful with security!)
    def read_file(filepath: str) -> dict:
        """Read a text file from the local filesystem.

        WARNING: This is a demonstration tool. In production, you should:
        - Implement proper access controls
        - Validate file paths
        - Restrict to specific directories
        - Handle permissions properly
        """
        try:
            # Basic security check - prevent directory traversal
            if ".." in filepath or filepath.startswith("/"):
                return {"error": "Invalid file path"}

            with open(filepath, 'r') as f:
                content = f.read()

            return {
                "filepath": filepath,
                "content": content,
                "size": len(content),
            }
        except FileNotFoundError:
            return {"error": f"File not found: {filepath}"}
        except Exception as e:
            return {"error": f"Error reading file: {str(e)}"}

    tools.append(Tool(
        name="read_file",
        description="Read the contents of a text file (restricted to safe paths)",
        parameters=[
            ToolParameter(
                name="filepath",
                type=ToolParameterType.STRING,
                description="Path to the file to read",
                required=True,
            ),
        ],
        function=read_file,
    ))

    # JSON parser tool
    def parse_json(json_string: str) -> dict:
        """Parse a JSON string and return the parsed object."""
        try:
            parsed = json.loads(json_string)
            return {
                "success": True,
                "data": parsed,
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON parsing error: {str(e)}",
            }

    tools.append(Tool(
        name="parse_json",
        description="Parse a JSON string and return the parsed object",
        parameters=[
            ToolParameter(
                name="json_string",
                type=ToolParameterType.STRING,
                description="The JSON string to parse",
                required=True,
            ),
        ],
        function=parse_json,
    ))

    # String manipulation tool
    def string_transform(text: str, operation: str) -> dict:
        """Transform a string using various operations."""
        operations = {
            "uppercase": lambda s: s.upper(),
            "lowercase": lambda s: s.lower(),
            "reverse": lambda s: s[::-1],
            "length": lambda s: len(s),
            "word_count": lambda s: len(s.split()),
        }

        if operation not in operations:
            return {"error": f"Unknown operation: {operation}"}

        result = operations[operation](text)
        return {
            "original": text,
            "operation": operation,
            "result": result,
        }

    tools.append(Tool(
        name="string_transform",
        description="Transform a string using various operations",
        parameters=[
            ToolParameter(
                name="text",
                type=ToolParameterType.STRING,
                description="The text to transform",
                required=True,
            ),
            ToolParameter(
                name="operation",
                type=ToolParameterType.STRING,
                description="The transformation to apply",
                required=True,
                enum=["uppercase", "lowercase", "reverse", "length", "word_count"],
            ),
        ],
        function=string_transform,
    ))

    return tools


def register_example_tools(tool_registry):
    """Register all example tools with a tool registry.

    Args:
        tool_registry: ToolRegistry instance to register tools with
    """
    example_tools = create_example_tools()
    for tool in example_tools:
        tool_registry.register_tool_direct(tool)
