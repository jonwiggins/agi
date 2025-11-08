"""
Example usage of the Recursive AGI agent system.

This demonstrates:
1. Task decomposition
2. Sub-agent spawning
3. Tool usage (web search, code execution, memory)
4. Result evaluation and validation
5. Execution tree visualization
"""
import os
from dotenv import load_dotenv
import json

from src.api.client import AnthropicClient
from src.memory.embeddings import EmbeddingGenerator
from src.memory.store import MemoryStore
from src.agent.recursive_agent import RecursiveAgent
from src.agent.enhanced_tools import create_enhanced_registry


def print_section(title: str):
    """Print a section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def print_tree(tree: dict, agent_id: str, indent: int = 0, visited: set = None):
    """Recursively print the execution tree."""
    if visited is None:
        visited = set()

    if agent_id in visited:
        return

    visited.add(agent_id)
    node = tree.get(agent_id, {})

    prefix = "  " * indent
    status = node.get("status", "unknown")
    task = node.get("task", "")[:60]

    print(f"{prefix}├─ [{status.value if hasattr(status, 'value') else status}] {task}...")

    for child_id in node.get("children", []):
        print_tree(tree, child_id, indent + 1, visited)


def main():
    """Run example tasks with the recursive agent."""
    # Load environment
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in environment")
        print("Please create a .env file with your API key")
        return

    print_section("Initializing Recursive AGI Agent")

    # Initialize components
    print("Setting up components...")
    embedding_generator = EmbeddingGenerator(api_key=api_key)
    memory_store = MemoryStore(
        persist_directory="./data/chroma",
        collection_name="recursive_agi_memories",
        embedding_generator=embedding_generator,
    )
    api_client = AnthropicClient(api_key=api_key)

    # Create enhanced tool registry
    tool_registry = create_enhanced_registry(memory_store=memory_store)

    # Create recursive agent
    agent = RecursiveAgent(
        api_client=api_client,
        memory_store=memory_store,
        tool_registry=tool_registry,
        max_depth=4,
        max_iterations=2,
        max_subagents=3,
    )

    print(f"✓ Agent initialized with {len(tool_registry.list_tools())} tools")
    print(f"  Tools: {', '.join(tool_registry.list_tools())}")

    # Example 1: Simple task (no decomposition)
    print_section("Example 1: Simple Calculation (Direct Execution)")

    task1 = "Calculate the sum of squares from 1 to 10"
    print(f"Task: {task1}\n")

    result1 = agent.execute_task(task1)

    print("Output:")
    print(result1.output)
    print(f"\nThoughts:\n{result1.thoughts[:300]}...")
    print(f"\nTools used: {[t['name'] for t in result1.tool_calls]}")

    # Example 2: Complex task requiring decomposition
    print_section("Example 2: Complex Research Task (With Decomposition)")

    task2 = """Research and analyze the latest developments in quantum computing.
    Provide a summary that includes:
    1. Recent breakthroughs
    2. Key companies and researchers
    3. Practical applications being explored
    4. Future predictions"""

    print(f"Task: {task2}\n")

    result2 = agent.execute_task(task2)

    print("Output:")
    print(result2.output[:500] + "...")
    print(f"\nTotal tool calls made: {len(result2.tool_calls)}")
    print(f"Tools used: {set([t['name'] for t in result2.tool_calls])}")

    print("\nExecution Tree:")
    print_tree(agent.get_execution_tree(), result2.agent_id)

    # Example 3: Task with code execution
    print_section("Example 3: Data Analysis Task (Code + Memory)")

    task3 = """Analyze the Fibonacci sequence:
    1. Generate the first 20 Fibonacci numbers using Python
    2. Calculate some interesting statistics (average, median, ratio between consecutive numbers)
    3. Store the insights in memory for future reference"""

    print(f"Task: {task3}\n")

    result3 = agent.execute_task(task3)

    print("Output:")
    print(result3.output)

    # Show execution details
    print("\nExecution Tree:")
    print_tree(agent.get_execution_tree(), result3.agent_id)

    # Example 4: Memory retrieval
    print_section("Example 4: Using Memory from Previous Tasks")

    task4 = "What did we learn about the Fibonacci sequence earlier?"
    print(f"Task: {task4}\n")

    result4 = agent.execute_task(task4)

    print("Output:")
    print(result4.output)

    # Show all thoughts from the root agent
    print_section("Agent Thoughts (Example 1)")
    thoughts = agent.get_agent_thoughts(result1.agent_id)
    for thought in thoughts[:5]:  # Show first 5
        print(f"[{thought.thought_type.upper()}] {thought.thought}")

    print_section("Summary")
    print("The recursive agent system demonstrates:")
    print("✓ Automatic task decomposition based on complexity")
    print("✓ Sub-agent spawning for parallel subtask execution")
    print("✓ Tool usage (web search, code execution, memory)")
    print("✓ Result evaluation and iterative refinement")
    print("✓ Context propagation through agent hierarchy")
    print("✓ Complete execution traceability")

    print("\n" + "="*70)
    print("Examples completed!")
    print("="*70)


if __name__ == "__main__":
    main()
