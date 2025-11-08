# AGI Platform for Claude Code

A containerized AGI (Artificial General Intelligence) platform designed for autonomous reasoning, learning, and task execution with persistent memory.

## Architecture Overview

The AGI Platform consists of two primary components orchestrated through Docker:

```
┌─────────────────────────────────────────────────────────┐
│                     AGI Platform                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐              ┌──────────────┐       │
│  │              │              │              │       │
│  │  Mind        │◄────────────►│  Database    │       │
│  │  Component   │              │  Component   │       │
│  │              │              │              │       │
│  └──────────────┘              └──────────────┘       │
│        │                              │               │
│        │                              │               │
│        ▼                              ▼               │
│   Reasoning &                    Knowledge &          │
│   Task Execution                 Memory Store         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. Mind Component

The **Mind** is the core reasoning engine of the AGI platform. It provides:

- **Autonomous Reasoning**: Multi-step task planning and execution
- **Context Management**: Maintains working memory and context windows
- **Tool Integration**: Connects to external tools and APIs
- **Learning Loop**: Continuous improvement through experience
- **Goal Management**: Tracks objectives and sub-goals
- **Decision Making**: Evaluates options and makes strategic choices

**Key Features:**
- Stateless processing with database-backed persistence
- API endpoint for task submission and monitoring
- WebSocket support for real-time interactions
- Plugin architecture for extensibility
- Model-agnostic design (supports multiple LLM backends)

### 2. Database Component

The **Database** provides persistent storage for the AGI's knowledge and memory:

- **Long-term Memory**: Stores experiences, learnings, and insights
- **Knowledge Graph**: Maintains relationships between concepts
- **Task History**: Tracks completed and in-progress tasks
- **Context Store**: Preserves conversation and session context
- **Vector Store**: Enables semantic search over memories
- **Episodic Memory**: Records sequences of events and outcomes

**Technology Stack:**
- PostgreSQL for structured data (tasks, sessions, metadata)
- Vector extension (pgvector) for embeddings and semantic search
- Redis for caching and real-time state management

## System Design

### Data Flow

1. **Task Input** → Mind receives task via API
2. **Reasoning** → Mind breaks down task and plans approach
3. **Memory Retrieval** → Queries database for relevant context
4. **Execution** → Performs actions using available tools
5. **Learning** → Stores outcomes and insights in database
6. **Memory Consolidation** → Periodic organization of knowledge

### Memory Architecture

```
Working Memory (Mind)
    ├─ Current Task Context
    ├─ Active Goals
    └─ Temporary Reasoning State
         │
         ▼
Long-term Memory (Database)
    ├─ Episodic Memory (experiences)
    ├─ Semantic Memory (knowledge)
    ├─ Procedural Memory (skills)
    └─ Meta Memory (self-awareness)
```

## Getting Started

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM recommended
- API key for LLM backend (OpenAI, Anthropic, etc.)

### Quick Start

1. **Clone and configure:**
   ```bash
   git clone <repository>
   cd agi
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Launch the platform:**
   ```bash
   docker-compose up -d
   ```

3. **Verify status:**
   ```bash
   docker-compose ps
   docker-compose logs -f mind
   ```

4. **Access the Mind API:**
   ```bash
   curl http://localhost:8000/health
   ```

### Configuration

Key environment variables in `.env`:

```bash
# Mind Configuration
MIND_PORT=8000
MODEL_PROVIDER=anthropic  # or openai, local, etc.
MODEL_NAME=claude-sonnet-4-5-20250929
API_KEY=your_api_key_here

# Database Configuration
POSTGRES_DB=agi_memory
POSTGRES_USER=agi
POSTGRES_PASSWORD=secure_password
REDIS_URL=redis://redis:6379

# Memory Configuration
MAX_CONTEXT_WINDOW=200000
MEMORY_RETENTION_DAYS=365
EMBEDDING_MODEL=text-embedding-3-small
```

## API Usage

### Submit a Task

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Analyze the codebase and suggest improvements",
    "context": "Focus on performance and maintainability",
    "priority": "high"
  }'
```

### Query Knowledge

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What patterns have we used for error handling?",
    "top_k": 5
  }'
```

### Get Task Status

```bash
curl http://localhost:8000/tasks/{task_id}
```

## Architecture Decisions

### Why Separate Mind and Database?

1. **Scalability**: Mind components can scale horizontally while database centralizes state
2. **Persistence**: Mind can restart/update without losing memory
3. **Security**: Database credentials isolated from processing layer
4. **Performance**: Optimized separately for compute vs. storage
5. **Modularity**: Components can be upgraded independently

### Memory Strategy

The platform implements a **hierarchical memory system**:

- **L1 (Working Memory)**: In-process, immediate context (~100K tokens)
- **L2 (Session Cache)**: Redis, recent interactions (~1M tokens worth)
- **L3 (Long-term Store)**: PostgreSQL, all historical data
- **L4 (Vector Search)**: Embeddings for semantic retrieval

### Learning Mechanism

The AGI learns through:
1. **Experience Recording**: Every task execution is logged
2. **Pattern Recognition**: Identifies successful strategies
3. **Abstraction**: Generalizes from specific cases
4. **Reflection**: Periodic self-analysis of performance
5. **Transfer**: Applies knowledge across domains

## Development

### Project Structure

```
agi/
├── docker-compose.yml       # Orchestration configuration
├── .env.example             # Environment template
├── mind/
│   ├── Dockerfile           # Mind container image
│   ├── requirements.txt     # Python dependencies
│   ├── src/
│   │   ├── main.py          # API server
│   │   ├── reasoning/       # Core reasoning engine
│   │   ├── memory/          # Memory interface
│   │   └── tools/           # Tool integrations
│   └── config/              # Configuration files
├── database/
│   ├── init/                # Database initialization scripts
│   └── schemas/             # Data models
└── docs/                    # Additional documentation
```

### Running Locally for Development

```bash
# Start with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# View logs
docker-compose logs -f mind

# Access database
docker-compose exec database psql -U agi -d agi_memory

# Run tests
docker-compose exec mind pytest
```

## Roadmap

### Phase 1: Foundation (Current)
- [x] Docker orchestration
- [ ] Basic mind reasoning engine
- [ ] PostgreSQL + pgvector setup
- [ ] Core API endpoints
- [ ] Simple memory storage/retrieval

### Phase 2: Intelligence
- [ ] Advanced reasoning strategies
- [ ] Goal decomposition
- [ ] Multi-agent collaboration
- [ ] Self-improvement loops
- [ ] Enhanced learning mechanisms

### Phase 3: Capabilities
- [ ] Tool discovery and learning
- [ ] Code generation and execution
- [ ] Knowledge graph reasoning
- [ ] Causal inference
- [ ] Planning under uncertainty

### Phase 4: Autonomy
- [ ] Self-directed exploration
- [ ] Meta-learning
- [ ] Transfer learning across domains
- [ ] Continuous background processing
- [ ] Proactive assistance

## Safety and Alignment

The platform includes several safety mechanisms:

1. **Sandboxing**: All code execution in isolated containers
2. **Audit Logging**: Complete record of all decisions and actions
3. **Rate Limiting**: Prevents runaway resource consumption
4. **Human Oversight**: Optional approval gates for critical operations
5. **Value Alignment**: Configurable goal constraints and ethics

## Contributing

We welcome contributions! Areas of interest:

- Reasoning algorithm improvements
- Memory efficiency optimizations
- New tool integrations
- Safety mechanisms
- Documentation and examples

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built with:
- Docker for containerization
- PostgreSQL + pgvector for storage
- Redis for caching
- FastAPI for the Mind API
- Anthropic Claude for reasoning

---

**Note**: This is an experimental platform for exploring AGI architectures. Using Claude Code to one-shot AGI development.
