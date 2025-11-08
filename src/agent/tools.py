"""
Tool registry and execution framework for the AGI agent.
"""
from typing import Callable, Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import inspect
import json


class ToolParameterType(str, Enum):
    """Types for tool parameters."""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""
    name: str
    type: ToolParameterType
    description: str
    required: bool = True
    enum: Optional[List[Any]] = None


@dataclass
class Tool:
    """Definition of a tool that can be called by the agent."""
    name: str
    description: str
    parameters: List[ToolParameter]
    function: Callable


class ToolRegistry:
    """Registry for managing and executing tools."""

    def __init__(self):
        """Initialize the tool registry."""
        self.tools: Dict[str, Tool] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: List[ToolParameter],
    ):
        """Decorator to register a function as a tool.

        Args:
            name: Name of the tool
            description: Description of what the tool does
            parameters: List of parameter definitions

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            tool = Tool(
                name=name,
                description=description,
                parameters=parameters,
                function=func,
            )
            self.tools[name] = tool
            return func
        return decorator

    def register_tool_direct(self, tool: Tool):
        """Register a tool directly without using a decorator.

        Args:
            tool: Tool instance to register
        """
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name.

        Args:
            name: Name of the tool

        Returns:
            Tool instance or None if not found
        """
        return self.tools.get(name)

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool with the given arguments.

        Args:
            name: Name of the tool to execute
            arguments: Dictionary of arguments to pass to the tool

        Returns:
            Result from the tool execution

        Raises:
            ValueError: If tool not found or execution fails
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found in registry")

        try:
            # Execute the tool function
            result = tool.function(**arguments)
            return result
        except Exception as e:
            raise ValueError(f"Error executing tool '{name}': {str(e)}")

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions in Anthropic API format.

        Returns:
            List of tool definition dicts
        """
        definitions = []
        for tool in self.tools.values():
            # Build input schema
            properties = {}
            required = []

            for param in tool.parameters:
                prop_def = {
                    "type": param.type.value,
                    "description": param.description,
                }
                if param.enum:
                    prop_def["enum"] = param.enum

                properties[param.name] = prop_def

                if param.required:
                    required.append(param.name)

            definition = {
                "name": tool.name,
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
            }
            definitions.append(definition)

        return definitions

    def list_tools(self) -> List[str]:
        """List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())


# Global tool registry instance
global_tool_registry = ToolRegistry()


def tool(name: str, description: str, parameters: List[ToolParameter]):
    """Convenience decorator to register a tool using the global registry.

    Args:
        name: Name of the tool
        description: Description of what the tool does
        parameters: List of parameter definitions

    Returns:
        Decorator function
    """
    return global_tool_registry.register_tool(name, description, parameters)
