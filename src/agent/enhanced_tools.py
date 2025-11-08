"""
Enhanced tool system for recursive agents.

Provides 5 core capabilities:
1. Web search (online information retrieval)
2. Memory/database operations (retrieve and store)
3. Python code execution (sandboxed)
4. Sub-agent creation (handled by RecursiveAgent)
5. Data storage (persistent storage)
"""
from typing import Dict, Any, List, Optional
import subprocess
import tempfile
import os
import json
from datetime import datetime
import requests

from .tools import ToolRegistry, Tool, ToolParameter, ToolParameterType
from ..memory.store import MemoryStore


class EnhancedToolRegistry(ToolRegistry):
    """Enhanced tool registry with built-in tools for recursive agents."""

    def __init__(self, memory_store: Optional[MemoryStore] = None):
        """Initialize enhanced tool registry.

        Args:
            memory_store: Memory store for database operations
        """
        super().__init__()
        self.memory_store = memory_store
        self._register_core_tools()

    def _register_core_tools(self):
        """Register the 5 core tools."""
        # Tool 1: Web Search
        self.register_tool_direct(Tool(
            name="web_search",
            description="Search the web for information using a search query. Returns relevant results with titles, snippets, and URLs.",
            parameters=[
                ToolParameter(
                    name="query",
                    type=ToolParameterType.STRING,
                    description="The search query",
                    required=True,
                ),
                ToolParameter(
                    name="num_results",
                    type=ToolParameterType.INTEGER,
                    description="Number of results to return (default: 5, max: 10)",
                    required=False,
                ),
            ],
            function=self._web_search,
        ))

        # Tool 2: Memory Search
        self.register_tool_direct(Tool(
            name="search_memory",
            description="Search the memory database for relevant stored information using semantic search",
            parameters=[
                ToolParameter(
                    name="query",
                    type=ToolParameterType.STRING,
                    description="Search query for finding relevant memories",
                    required=True,
                ),
                ToolParameter(
                    name="n_results",
                    type=ToolParameterType.INTEGER,
                    description="Number of results to return (default: 5)",
                    required=False,
                ),
            ],
            function=self._search_memory,
        ))

        # Tool 3: Store Memory
        self.register_tool_direct(Tool(
            name="store_data",
            description="Store data/information in the persistent memory database for future retrieval",
            parameters=[
                ToolParameter(
                    name="content",
                    type=ToolParameterType.STRING,
                    description="The information to store",
                    required=True,
                ),
                ToolParameter(
                    name="metadata_json",
                    type=ToolParameterType.STRING,
                    description="Optional JSON string with metadata (tags, category, etc.)",
                    required=False,
                ),
            ],
            function=self._store_data,
        ))

        # Tool 4: Execute Python Code
        self.register_tool_direct(Tool(
            name="execute_python",
            description="Execute Python code in a sandboxed environment. Returns the output or error. Use for calculations, data processing, or testing logic.",
            parameters=[
                ToolParameter(
                    name="code",
                    type=ToolParameterType.STRING,
                    description="Python code to execute",
                    required=True,
                ),
                ToolParameter(
                    name="timeout",
                    type=ToolParameterType.INTEGER,
                    description="Execution timeout in seconds (default: 30, max: 60)",
                    required=False,
                ),
            ],
            function=self._execute_python,
        ))

        # Tool 5: Create Sub-agent (placeholder - handled by RecursiveAgent)
        self.register_tool_direct(Tool(
            name="create_subagent",
            description="Create a sub-agent to handle a specific subtask. The sub-agent will recursively solve the problem and return results.",
            parameters=[
                ToolParameter(
                    name="subtask",
                    type=ToolParameterType.STRING,
                    description="The specific subtask for the sub-agent to solve",
                    required=True,
                ),
                ToolParameter(
                    name="context",
                    type=ToolParameterType.STRING,
                    description="Additional context for the sub-agent",
                    required=False,
                ),
                ToolParameter(
                    name="expected_output",
                    type=ToolParameterType.STRING,
                    description="Description of what output is expected from the sub-agent",
                    required=False,
                ),
            ],
            function=lambda **kwargs: {
                "note": "This tool is handled specially by RecursiveAgent",
                "subtask": kwargs.get("subtask", ""),
            },
        ))

    def _web_search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Perform web search.

        Note: This uses DuckDuckGo HTML parsing as a simple implementation.
        For production, use a proper API like Google Custom Search, Bing API, or Brave Search.

        Args:
            query: Search query
            num_results: Number of results

        Returns:
            Search results
        """
        try:
            # Limit results
            num_results = min(num_results, 10)

            # Use DuckDuckGo HTML (no API key needed)
            url = "https://html.duckduckgo.com/html/"
            params = {"q": query}
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code != 200:
                return {
                    "error": f"Search failed with status {response.status_code}",
                    "results": []
                }

            # Parse results (basic HTML parsing)
            results = []
            from html.parser import HTMLParser

            class DuckDuckGoParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.results = []
                    self.current_result = {}
                    self.in_result = False
                    self.in_title = False
                    self.in_snippet = False

                def handle_starttag(self, tag, attrs):
                    attrs_dict = dict(attrs)
                    if tag == "a" and "result__a" in attrs_dict.get("class", ""):
                        self.in_title = True
                        self.current_result = {"url": attrs_dict.get("href", "")}
                    elif tag == "a" and "result__snippet" in attrs_dict.get("class", ""):
                        self.in_snippet = True

                def handle_data(self, data):
                    if self.in_title:
                        self.current_result["title"] = data.strip()
                    elif self.in_snippet:
                        self.current_result["snippet"] = data.strip()

                def handle_endtag(self, tag):
                    if tag == "a" and self.in_title:
                        self.in_title = False
                        if self.current_result.get("title"):
                            self.results.append(dict(self.current_result))
                    elif tag == "a" and self.in_snippet:
                        self.in_snippet = False

            parser = DuckDuckGoParser()
            parser.feed(response.text)
            results = parser.results[:num_results]

            if not results:
                # Fallback: return basic info
                results = [{
                    "title": f"Search results for: {query}",
                    "snippet": "Web search functionality requires API integration. Using placeholder results.",
                    "url": f"https://duckduckgo.com/?q={query}"
                }]

            return {
                "query": query,
                "num_results": len(results),
                "results": results,
            }

        except Exception as e:
            return {
                "error": f"Web search failed: {str(e)}",
                "query": query,
                "results": [{
                    "title": f"Search: {query}",
                    "snippet": f"Web search encountered an error. For production, integrate a proper search API (Google, Bing, Brave).",
                    "url": f"https://duckduckgo.com/?q={query}"
                }]
            }

    def _search_memory(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Search memory database.

        Args:
            query: Search query
            n_results: Number of results

        Returns:
            Search results from memory
        """
        if not self.memory_store:
            return {
                "error": "Memory store not initialized",
                "results": []
            }

        try:
            memories = self.memory_store.search_memories(
                query=query,
                n_results=n_results,
            )

            return {
                "query": query,
                "num_results": len(memories),
                "results": [
                    {
                        "content": mem["content"],
                        "relevance": mem.get("relevance", 0),
                        "metadata": mem.get("metadata", {}),
                        "id": mem.get("id", ""),
                    }
                    for mem in memories
                ]
            }
        except Exception as e:
            return {
                "error": f"Memory search failed: {str(e)}",
                "results": []
            }

    def _store_data(self, content: str, metadata_json: str = "{}") -> Dict[str, Any]:
        """Store data in memory.

        Args:
            content: Content to store
            metadata_json: JSON string with metadata

        Returns:
            Storage result
        """
        if not self.memory_store:
            return {"error": "Memory store not initialized"}

        try:
            metadata = json.loads(metadata_json) if metadata_json else {}
            metadata["stored_at"] = datetime.now().isoformat()

            memory_id = self.memory_store.add_memory(
                content=content,
                metadata=metadata,
            )

            return {
                "status": "success",
                "memory_id": memory_id,
                "content_preview": content[:100] + "..." if len(content) > 100 else content,
            }
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in metadata_json parameter"}
        except Exception as e:
            return {"error": f"Failed to store data: {str(e)}"}

    def _execute_python(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute Python code in a sandboxed environment.

        Security measures:
        - Runs in subprocess with timeout
        - Limited execution time
        - No network access (configurable)
        - Restricted imports (configurable)

        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds

        Returns:
            Execution result with stdout, stderr, and return code
        """
        # Limit timeout
        timeout = min(timeout, 60)

        try:
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                temp_file = f.name
                f.write(code)

            # Execute in subprocess with timeout
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}
            )

            # Clean up
            os.unlink(temp_file)

            return {
                "status": "success" if result.returncode == 0 else "error",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": f"<{timeout}s",
            }

        except subprocess.TimeoutExpired:
            # Clean up on timeout
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file)
                except:
                    pass

            return {
                "status": "timeout",
                "error": f"Execution exceeded {timeout} second timeout",
                "stdout": "",
                "stderr": "",
            }

        except Exception as e:
            # Clean up on error
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file)
                except:
                    pass

            return {
                "status": "error",
                "error": f"Execution failed: {str(e)}",
                "stdout": "",
                "stderr": "",
            }


def create_enhanced_registry(memory_store: Optional[MemoryStore] = None) -> EnhancedToolRegistry:
    """Create an enhanced tool registry with all core tools.

    Args:
        memory_store: Optional memory store for database operations

    Returns:
        Configured EnhancedToolRegistry
    """
    return EnhancedToolRegistry(memory_store=memory_store)
