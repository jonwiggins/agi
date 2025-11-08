# AGI Platform

An advanced recursive AGI platform with hierarchical sub-agents, built on Anthropic's Claude API and local embedding-based memory storage.

## 🚀 New: Recursive Sub-Agent Architecture

The platform now features a **recursive agent system** that:
- 🧠 **Auto-decomposes** complex tasks into subtasks
- 🤖 **Spawns sub-agents** to solve each piece recursively
- ✅ **Evaluates & refines** results with accept/reject loops
- 🔍 **Ultrathink mode** for deep task analysis
- 🌳 **Full execution trees** for complete traceability

## Features

- **Recursive Task Decomposition**: Automatically breaks down complex problems into manageable subtasks
- **Sub-Agent Spawning**: Hierarchical agent system with intelligent delegation
- **Evaluation & Refinement**: Accept/reject loops with iterative improvement
- **Enhanced Tools**: Web search, code execution, memory operations, and more
- **Long-term Memory**: Persistent memory across conversations using ChromaDB
- **Ultrathink Analysis**: Deep reasoning before execution
- **FastAPI Server**: RESTful API for interacting with the AGI system
- **Docker Ready**: Production-ready containerization

## Architecture

```
agi/
├── src/
│   ├── memory/          # Memory storage with ChromaDB
│   ├── api/             # Anthropic API client wrapper
│   ├── agent/           # Core AGI agent logic
│   │   ├── recursive_agent.py    # NEW: Recursive sub-agent system
│   │   ├── enhanced_tools.py     # NEW: 5 core tools
│   │   ├── core.py               # Original agent (still available)
│   │   └── tools.py              # Tool framework
│   └── server/          # FastAPI server
│       ├── recursive_main.py     # NEW: Recursive server (default)
│       └── main.py               # Original server
├── tools/               # Example and custom tools
└── data/                # Persistent data storage
```

## Two Architectures Available

1. **Recursive Agent** (default) - For complex, multi-step tasks
2. **Original Agent** - For simple, direct interactions

See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for details.

## Quick Start with Docker (Recommended)

The easiest way to run the AGI platform is using Docker:

```bash
# 1. Clone the repository
git clone <repository-url>
cd agi

# 2. Set up configuration
make setup
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Start the platform
make up

# 4. View logs
make logs

# 5. Access the API at http://localhost:8000/docs
```

### Docker Commands

| Command | Description |
|---------|-------------|
| `make setup` | First-time setup (creates .env and directories) |
| `make build` | Build Docker images |
| `make up` | Start the platform in production mode |
| `make down` | Stop the platform |
| `make restart` | Restart the platform |
| `make logs` | View container logs |
| `make dev-up` | Start with hot-reload for development |
| `make shell` | Open shell in container |
| `make clean` | Clean up containers and volumes |

### Docker Compose Files

- **docker-compose.yml**: Production configuration with optimized settings
- **docker-compose.dev.yml**: Development configuration with hot-reloading

### Testing the Docker Deployment

```bash
# Start the platform
make up

# Test the health endpoint
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello! What is 5 + 3?"}'

# View API documentation
open http://localhost:8000/docs
```

## Installation

### Prerequisites

- Python 3.10 or higher
- Anthropic API key

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd agi
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

### Starting the Server

```bash
python -m src.server.main
```

The server will start on `http://localhost:8000` by default.

### API Endpoints

#### Chat with the Agent

```bash
POST /chat
```

Request body:
```json
{
  "message": "What's the weather like today?",
  "conversation_history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help you?"}
  ],
  "store_in_memory": true
}
```

Response:
```json
{
  "response": "I don't have access to real-time weather data...",
  "tool_calls": [],
  "memories_used": [],
  "metadata": {
    "iterations": 1,
    "stop_reason": "end_turn"
  }
}
```

#### Add a Memory

```bash
POST /memory
```

Request body:
```json
{
  "content": "The user's favorite color is blue",
  "metadata": {
    "category": "preference",
    "user_id": "user123"
  }
}
```

#### Search Memories

```bash
POST /memory/search
```

Request body:
```json
{
  "query": "What is the user's favorite color?",
  "n_results": 5
}
```

#### List Available Tools

```bash
GET /tools
```

### Using the Python API

```python
from src.api.client import AnthropicClient
from src.memory.embeddings import EmbeddingGenerator
from src.memory.store import MemoryStore
from src.agent.core import AGIAgent
from src.agent.tools import ToolRegistry
from tools.examples import register_example_tools
import os

# Initialize components
api_key = os.getenv("ANTHROPIC_API_KEY")

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

# Create agent
agent = AGIAgent(
    api_client=api_client,
    memory_store=memory_store,
    tool_registry=tool_registry,
)

# Chat with the agent
response = agent.process_message("What's 25 + 17?")
print(response.content)

# Add a memory
agent.add_memory(
    content="The user loves Python programming",
    metadata={"category": "interest"}
)

# Search memories
memories = agent.search_memories("What does the user like?")
for mem in memories:
    print(f"Memory: {mem['content']} (relevance: {mem['relevance']:.2f})")
```

## Creating Custom Tools

Tools extend the agent's capabilities. Here's how to create a custom tool:

```python
from src.agent.tools import Tool, ToolParameter, ToolParameterType

def my_custom_tool(param1: str, param2: int) -> dict:
    """Your tool implementation."""
    return {
        "result": f"Processed {param1} with {param2}",
    }

# Create tool definition
custom_tool = Tool(
    name="my_custom_tool",
    description="Description of what the tool does",
    parameters=[
        ToolParameter(
            name="param1",
            type=ToolParameterType.STRING,
            description="Description of param1",
            required=True,
        ),
        ToolParameter(
            name="param2",
            type=ToolParameterType.INTEGER,
            description="Description of param2",
            required=True,
        ),
    ],
    function=my_custom_tool,
)

# Register with the agent
tool_registry.register_tool_direct(custom_tool)
```

## Configuration

Environment variables (`.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Required |
| `CHROMA_PERSIST_DIRECTORY` | ChromaDB data directory | `./data/chroma` |
| `MEMORY_COLLECTION_NAME` | ChromaDB collection name | `agi_memories` |
| `DEFAULT_MODEL` | Default Claude model | `claude-sonnet-4-5-20250929` |
| `MAX_MEMORY_RESULTS` | Max memories to retrieve | `5` |
| `MEMORY_RELEVANCE_THRESHOLD` | Min relevance score | `0.7` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |

## Memory System

The platform uses ChromaDB for vector-based memory storage. Memories are embedded and can be retrieved based on semantic similarity.

**Note**: The current implementation uses a placeholder embedding function. For production use, integrate a real embedding model such as:
- Voyage AI
- OpenAI embeddings
- Sentence Transformers

To integrate a real embedding model, modify `src/memory/embeddings.py`.

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/ tools/
ruff check src/ tools/
```

## Extending the Platform

### Adding New Features

1. **Custom Memory Types**: Extend `MemoryStore` to support different memory categorization
2. **Advanced Tool Systems**: Implement tool chaining, conditional execution, or parallel execution
3. **Multi-Agent Systems**: Create multiple specialized agents that collaborate
4. **Web Interface**: Build a frontend using the FastAPI server
5. **Streaming Responses**: Use the `create_message_stream` method for real-time responses

### Security Considerations

- **API Key Protection**: Never commit your `.env` file
- **Tool Security**: Validate all tool inputs and restrict file system access
- **Memory Privacy**: Implement access controls for sensitive memories
- **Rate Limiting**: Add rate limiting to API endpoints for production use

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Acknowledgments

Built with:
- [Anthropic Claude](https://www.anthropic.com/) - Advanced language models
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [ChromaDB](https://www.trychroma.com/) - Vector database for embeddings
