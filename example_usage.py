"""
Example script demonstrating how to use the AGI platform.

This script shows:
1. Setting up the agent
2. Chatting with the agent
3. Using tools
4. Working with memories
"""
import os
from dotenv import load_dotenv

from src.api.client import AnthropicClient
from src.memory.embeddings import EmbeddingGenerator
from src.memory.store import MemoryStore
from src.agent.core import AGIAgent
from src.agent.tools import ToolRegistry
from tools.examples import register_example_tools


def main():
    """Run the example usage script."""
    # Load environment variables
    load_dotenv()

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment variables.")
        print("Please create a .env file with your API key.")
        return

    print("Initializing AGI platform...")
    print("-" * 60)

    # Initialize components
    embedding_generator = EmbeddingGenerator(api_key=api_key)
    memory_store = MemoryStore(
        persist_directory="./data/chroma",
        collection_name="agi_memories",
        embedding_generator=embedding_generator,
    )
    api_client = AnthropicClient(api_key=api_key)
    tool_registry = ToolRegistry()

    # Register example tools
    register_example_tools(tool_registry)
    print(f"Registered {len(tool_registry.list_tools())} tools:")
    for tool_name in tool_registry.list_tools():
        print(f"  - {tool_name}")
    print()

    # Create agent
    agent = AGIAgent(
        api_client=api_client,
        memory_store=memory_store,
        tool_registry=tool_registry,
    )

    print("AGI agent initialized successfully!")
    print("-" * 60)
    print()

    # Example 1: Simple conversation
    print("Example 1: Simple conversation")
    print("-" * 60)
    response = agent.process_message(
        "Hello! My name is Alex and I'm a software engineer.",
        store_in_memory=True
    )
    print(f"User: Hello! My name is Alex and I'm a software engineer.")
    print(f"Agent: {response.content}")
    print()

    # Example 2: Using tools (calculator)
    print("Example 2: Using the calculator tool")
    print("-" * 60)
    response = agent.process_message(
        "What is 42 multiplied by 17?",
        store_in_memory=False
    )
    print(f"User: What is 42 multiplied by 17?")
    print(f"Agent: {response.content}")
    if response.tool_calls:
        print(f"Tools used: {[tc['name'] for tc in response.tool_calls]}")
    print()

    # Example 3: Testing memory recall
    print("Example 3: Testing memory recall")
    print("-" * 60)
    response = agent.process_message(
        "What's my name and what do I do?",
        store_in_memory=False
    )
    print(f"User: What's my name and what do I do?")
    print(f"Agent: {response.content}")
    if response.memories_used:
        print(f"Memories retrieved: {len(response.memories_used)}")
        for mem in response.memories_used[:2]:  # Show first 2
            print(f"  - {mem['content'][:60]}... (relevance: {mem['relevance']:.2f})")
    print()

    # Example 4: Adding custom memory
    print("Example 4: Adding a custom memory")
    print("-" * 60)
    memory_id = agent.add_memory(
        content="Alex's favorite programming language is Python",
        metadata={"category": "preference", "topic": "programming"}
    )
    print(f"Added memory with ID: {memory_id}")
    print()

    # Example 5: Searching memories
    print("Example 5: Searching memories")
    print("-" * 60)
    memories = agent.search_memories("What does Alex like?", n_results=3)
    print(f"Search query: 'What does Alex like?'")
    print(f"Found {len(memories)} relevant memories:")
    for i, mem in enumerate(memories, 1):
        print(f"{i}. {mem['content']} (relevance: {mem['relevance']:.2f})")
    print()

    # Example 6: Tool with string transformation
    print("Example 6: Using string transformation tool")
    print("-" * 60)
    response = agent.process_message(
        "Please reverse the text 'Hello World'",
        store_in_memory=False
    )
    print(f"User: Please reverse the text 'Hello World'")
    print(f"Agent: {response.content}")
    print()

    print("-" * 60)
    print("Examples completed!")
    print()
    print("Next steps:")
    print("1. Start the FastAPI server: python -m src.server.main")
    print("2. Create your own custom tools in tools/")
    print("3. Explore the API at http://localhost:8000/docs")


if __name__ == "__main__":
    main()
