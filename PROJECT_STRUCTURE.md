# AGI Platform - Project Structure

Complete overview of the project structure and file organization.

## Directory Tree

```
agi/
├── src/                           # Main application code
│   ├── __init__.py
│   ├── memory/                    # Memory storage system
│   │   ├── __init__.py
│   │   ├── embeddings.py         # Embedding generation
│   │   └── store.py              # ChromaDB vector store
│   ├── api/                       # Anthropic API client
│   │   ├── __init__.py
│   │   └── client.py             # API wrapper with streaming
│   ├── agent/                     # AGI agent core
│   │   ├── __init__.py
│   │   ├── core.py               # Main agent logic
│   │   └── tools.py              # Tool registry framework
│   └── server/                    # FastAPI server
│       ├── __init__.py
│       └── main.py               # API endpoints
│
├── tools/                         # Custom tools
│   ├── __init__.py
│   └── examples.py               # Example tool implementations
│
├── scripts/                       # Utility scripts
│   ├── __init__.py
│   ├── docker-entrypoint.sh      # Container startup script
│   ├── healthcheck.sh            # Health check script
│   └── test_docker.sh            # Docker deployment tests
│
├── data/                          # Persistent data (not in git)
│   └── chroma/                   # ChromaDB storage
│
├── Docker Files
│   ├── Dockerfile                # Multi-stage container build
│   ├── docker-compose.yml        # Production orchestration
│   ├── docker-compose.dev.yml    # Development orchestration
│   └── .dockerignore             # Docker ignore patterns
│
├── Configuration Files
│   ├── .env.example              # Environment template
│   ├── .env.docker               # Docker-specific template
│   ├── .gitignore                # Git ignore patterns
│   ├── pyproject.toml            # Python project config
│   └── requirements.txt          # Python dependencies
│
├── Documentation
│   ├── README.md                 # Main documentation
│   ├── QUICKSTART.md             # Quick start guide
│   ├── DOCKER.md                 # Docker deployment guide
│   └── PROJECT_STRUCTURE.md      # This file
│
├── Build & Automation
│   └── Makefile                  # Docker command shortcuts
│
└── Examples
    └── example_usage.py          # Usage examples
```

## Core Components

### Memory System (`src/memory/`)

**embeddings.py**
- `EmbeddingGenerator`: Generates embeddings for semantic search
- Currently uses placeholder (integrate real embedding API for production)
- Supports Anthropic, OpenAI, or Sentence Transformers

**store.py**
- `MemoryStore`: ChromaDB-based vector database interface
- Operations: add, search, retrieve, delete memories
- Automatic persistence to disk

### API Layer (`src/api/`)

**client.py**
- `AnthropicClient`: Wrapper for Anthropic API
- Streaming support for real-time responses
- Tool calling integration
- Message formatting utilities

### Agent System (`src/agent/`)

**core.py**
- `AGIAgent`: Main agent orchestration
- Memory-enhanced conversation
- Tool execution loop
- Automatic memory storage

**tools.py**
- `ToolRegistry`: Tool management system
- `Tool`: Tool definition dataclass
- Parameter validation
- Automatic Anthropic API format conversion

### Server Layer (`src/server/`)

**main.py**
- FastAPI application
- REST endpoints for chat, memory, tools
- CORS configuration
- Health checks
- OpenAPI documentation

### Tools (`tools/`)

**examples.py**
- Calculator (arithmetic operations)
- Current time getter
- File reader (with security constraints)
- JSON parser
- String transformations

## Docker Stack

### Dockerfile
- **Builder stage**: Compiles dependencies
- **Runtime stage**: Minimal production image
- Non-root user (security)
- Health checks
- Entrypoint script

### docker-compose.yml (Production)
- Single service deployment
- Volume mounts for persistence
- Resource limits (2 CPU, 4GB RAM)
- Network isolation
- Health monitoring

### docker-compose.dev.yml (Development)
- Hot-reload enabled
- Source code mounted
- Debug mode
- Interactive mode

## Scripts

### docker-entrypoint.sh
- Environment validation
- Directory initialization
- Configuration checks
- Service startup

### test_docker.sh
- Health endpoint test
- API endpoint tests
- Tool execution tests
- Memory operation tests
- Comprehensive deployment verification

## Configuration

### Environment Variables

| File | Purpose |
|------|---------|
| `.env.example` | Template for local development |
| `.env.docker` | Template for Docker deployment |
| `.env` | Active configuration (not in git) |

### Dependencies

| File | Purpose |
|------|---------|
| `pyproject.toml` | Modern Python package config |
| `requirements.txt` | Pip dependency list |

## Data Flow

```
User Request
    ↓
FastAPI Endpoint (/chat)
    ↓
AGIAgent.process_message()
    ↓
Memory Retrieval (ChromaDB)
    ↓
Enhanced Prompt Construction
    ↓
Anthropic API Call
    ↓
Tool Execution (if needed)
    ↓
Response Generation
    ↓
Memory Storage
    ↓
Return to User
```

## Key Design Patterns

1. **Dependency Injection**: Components passed as constructor parameters
2. **Repository Pattern**: MemoryStore abstracts ChromaDB
3. **Facade Pattern**: AnthropicClient simplifies API
4. **Strategy Pattern**: Tool registry for extensibility
5. **Builder Pattern**: Message and prompt construction

## Security Features

- Non-root container user
- API key environment variables
- Input validation on tools
- CORS configuration
- Health check endpoints
- Resource limits

## Extensibility Points

1. **Custom Tools**: Add to `tools/` directory
2. **Embedding Models**: Replace in `src/memory/embeddings.py`
3. **Memory Backends**: Swap `MemoryStore` implementation
4. **Additional Agents**: Create new agent classes
5. **Middleware**: Add to FastAPI app

## Development Workflow

```bash
# 1. Setup
make setup

# 2. Configure
edit .env

# 3. Develop (hot-reload)
make dev-up

# 4. Test
make test-docker

# 5. Production
make build && make up

# 6. Monitor
make logs
make status
```

## Production Considerations

- [ ] Integrate real embedding API
- [ ] Add authentication/authorization
- [ ] Implement rate limiting
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure reverse proxy (nginx)
- [ ] Enable HTTPS
- [ ] Set up backup automation
- [ ] Implement API key rotation
- [ ] Add comprehensive logging
- [ ] Configure alerts

## File Counts

- Python files: 11
- Docker files: 3
- Scripts: 3
- Documentation: 4
- Configuration: 6

## Total Lines of Code

- Core application: ~1,800 lines
- Example tools: ~200 lines
- Tests: ~100 lines
- Docker/Config: ~300 lines
- Documentation: ~1,000 lines

---

Last updated: 2025-11-08
