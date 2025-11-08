# AGI Platform - Recursive Subagent Architecture

A recursive AGI system that solves complex problems by dynamically decomposing them into subproblems, spawning specialized subagents, and synthesizing solutions through a tree of collaborative agents.

## Core Concept

The AGI operates as a **recursive tree of agents**, where:

1. A **root agent** receives a complex task
2. It **decomposes** the task into smaller, manageable subtasks
3. For each subtask, it **spawns a subagent** with specific context
4. Subagents can **recursively spawn their own subagents**
5. Results **bubble up** through accept/reject evaluation
6. Each agent adds **synthesis and insights** before returning results

```
                    ┌─────────────────┐
                    │   Root Agent    │
                    │  "Build a web   │
                    │   application"  │
                    └────────┬────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
         ┌──────▼──────┐ ┌──▼─────────┐ ┌▼──────────┐
         │  Agent 1.1  │ │ Agent 1.2  │ │Agent 1.3  │
         │  "Design    │ │ "Backend"  │ │"Frontend" │
         │   Database" │ └────────────┘ └───────────┘
         └──────┬──────┘
                │
          ┌─────┼─────┐
          │     │     │
      ┌───▼──┐ ┌▼───┐┌▼────┐
      │ 1.1.1│ │1.1.2││1.1.3│
      │Schema│ │Index││Query│
      └──────┘ └────┘└─────┘
```

## Architecture Overview

### The Recursive Pattern

Each agent in the tree follows this algorithm:

```python
def solve_task(task, context):
    # 1. Analyze the task
    understanding = analyze(task, context)

    # 2. Decide: Can I solve this directly?
    if is_atomic(task):
        # Solve directly using tools
        result = use_tools(task)
        return {"result": result, "thoughts": synthesis}

    # 3. Decompose into subtasks
    subtasks = decompose(task)

    # 4. Spawn subagents for each subtask
    subagent_results = []
    for subtask in subtasks:
        subagent = spawn_agent(subtask, context)
        result = subagent.solve_task(subtask, context)

        # 5. Evaluate the result
        if evaluate(result) == "accept":
            subagent_results.append(result)
        else:
            # Reject and request changes
            feedback = generate_feedback(result)
            result = subagent.solve_task(subtask, context, feedback)
            subagent_results.append(result)

    # 6. Synthesize results
    final_result = synthesize(subagent_results)

    # 7. Return with additional insights
    return {
        "result": final_result,
        "thoughts": my_synthesis,
        "learnings": insights
    }
```

## Agent Capabilities

### Context Inheritance

Each agent receives:

1. **Global Context**: The original high-level goal and constraints
2. **Local Task**: Its specific subtask to solve
3. **Parent Guidance**: Instructions or constraints from parent agent
4. **Feedback Loop**: Revision requests if work is rejected

Example:
```json
{
  "global_context": {
    "goal": "Build a scalable e-commerce platform",
    "constraints": ["Must use Python", "Budget: $10k", "Timeline: 3 months"],
    "requirements": ["Handle 10k users", "Payment processing", "Inventory"]
  },
  "local_task": {
    "objective": "Design the database schema for products and inventory",
    "deliverables": ["ERD diagram", "SQL schema", "Migration plan"]
  },
  "parent_guidance": {
    "preferences": ["Use PostgreSQL", "Normalize to 3NF"],
    "avoid": ["NoSQL databases"]
  }
}
```

### Tool System

Each agent has access to **5 core tools**:

#### 1. Web Search
```python
web_search(query: str, num_results: int = 5) -> List[SearchResult]
```
Search the internet for information, documentation, or solutions.

**Use cases:**
- Research best practices
- Find documentation
- Discover existing solutions
- Gather domain knowledge

#### 2. Database Query
```python
db_query(query: str, filters: dict = None) -> QueryResult
```
Query the memory database for past experiences, learnings, or stored knowledge.

**Use cases:**
- Recall similar past tasks
- Retrieve stored solutions
- Access organizational knowledge
- Find relevant experiences

#### 3. Code Execution
```python
execute_code(code: str, language: str = "python", timeout: int = 30) -> ExecutionResult
```
Execute code in a sandboxed environment.

**Use cases:**
- Test hypotheses
- Validate solutions
- Prototype implementations
- Run experiments

#### 4. Create Subagent
```python
create_subagent(
    task: str,
    context: dict,
    constraints: dict = None,
    timeout: int = 300
) -> SubagentResult
```
Spawn a new subagent to handle a decomposed subtask.

**Use cases:**
- Delegate complex subtasks
- Parallelize work
- Specialize problem-solving
- Recursive decomposition

#### 5. Store Data
```python
store_data(
    data: Any,
    category: str,
    metadata: dict = None,
    embedding: bool = True
) -> StorageResult
```
Persist data, learnings, or solutions to the database.

**Use cases:**
- Save successful solutions
- Record learnings
- Build knowledge base
- Enable future retrieval

## Evaluation & Feedback Loop

### Accept/Reject Mechanism

When a subagent returns a result, the parent agent evaluates it:

```python
class EvaluationResult:
    decision: Literal["accept", "reject", "revise"]
    score: float  # 0.0 to 1.0
    feedback: str
    required_changes: List[str]
    reasoning: str
```

**Accept Criteria:**
- Solution meets requirements
- Quality exceeds threshold
- No critical issues found

**Reject/Revise Criteria:**
- Missing requirements
- Quality below threshold
- Errors or inconsistencies
- Better approach available

### Revision Process

```
┌─────────────┐
│   Parent    │
│   Agent     │
└──────┬──────┘
       │ Task
       ▼
┌─────────────┐
│  Subagent   │──────► Result v1
└─────────────┘
       ▲              │
       │              ▼
       │         ┌──────────┐
       │         │ Evaluate │
       │         └────┬─────┘
       │              │
       │         Reject + Feedback
       │              │
       └──────────────┘
       │
       ▼
   Result v2 ──────► Evaluate ──► Accept
```

## System Components

### 1. Mind (Agent Orchestrator)

The Mind service manages the agent tree:

- **Agent Lifecycle**: Creation, execution, termination
- **Tree Management**: Parent-child relationships, depth limits
- **Resource Allocation**: CPU, memory, timeout management
- **Tool Routing**: Dispatches tool calls to appropriate handlers
- **Result Synthesis**: Combines subagent outputs

**Docker Service**: `mind`
- FastAPI server on port 8000
- WebSocket for real-time agent updates
- Async agent execution
- Tree visualization endpoints

### 2. Database (Memory & State)

Stores agent trees, results, and knowledge:

**Tables:**
- `agent_trees`: Tree structure and relationships
- `agent_executions`: Individual agent runs and results
- `task_decompositions`: How tasks were broken down
- `tool_calls`: History of all tool invocations
- `knowledge_store`: Persistent knowledge with embeddings
- `evaluation_history`: Accept/reject decisions and feedback

**Docker Service**: `database`
- PostgreSQL 16 with pgvector
- Stores full execution traces
- Enables semantic search over past solutions
- Supports audit and replay

### 3. Redis (Agent Communication)

Fast inter-agent communication:

- **Message Queue**: Parent-child communication
- **State Cache**: Active agent states
- **Lock Management**: Prevents duplicate work
- **Result Buffer**: Temporary result storage

## Getting Started

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM recommended
- API key for LLM backend (Anthropic Claude recommended)

### Quick Start

1. **Clone and configure:**
   ```bash
   git clone <repository>
   cd agi
   cp .env.example .env
   # Edit .env - add your ANTHROPIC_API_KEY
   ```

2. **Launch the platform:**
   ```bash
   docker-compose up -d
   ```

3. **Submit a task:**
   ```bash
   curl -X POST http://localhost:8000/tasks \
     -H "Content-Type: application/json" \
     -d '{
       "task": "Create a REST API for a todo list application",
       "context": {
         "requirements": ["CRUD operations", "Authentication", "PostgreSQL"],
         "constraints": ["Use FastAPI", "Follow best practices"]
       }
     }'
   ```

4. **Watch the agent tree in real-time:**
   ```bash
   # WebSocket connection
   wscat -c ws://localhost:8000/ws/tasks/{task_id}
   ```

5. **View the execution tree:**
   ```bash
   curl http://localhost:8000/tasks/{task_id}/tree
   ```

## API Reference

### Submit Task

```http
POST /tasks
Content-Type: application/json

{
  "task": "Your complex task description",
  "context": {
    "requirements": ["list", "of", "requirements"],
    "constraints": ["list", "of", "constraints"],
    "preferences": {}
  },
  "max_depth": 5,
  "max_agents": 50,
  "timeout": 3600
}
```

**Response:**
```json
{
  "task_id": "uuid",
  "status": "processing",
  "agent_tree_id": "uuid",
  "created_at": "2025-11-08T10:00:00Z"
}
```

### Get Task Status

```http
GET /tasks/{task_id}
```

**Response:**
```json
{
  "task_id": "uuid",
  "status": "completed",
  "result": {
    "output": "Final synthesized result",
    "insights": ["Learning 1", "Learning 2"],
    "confidence": 0.95
  },
  "metrics": {
    "total_agents": 12,
    "tree_depth": 3,
    "execution_time_seconds": 45.3,
    "tool_calls": {
      "web_search": 5,
      "db_query": 3,
      "code_execution": 8,
      "create_subagent": 11,
      "store_data": 4
    }
  }
}
```

### View Agent Tree

```http
GET /tasks/{task_id}/tree
```

Returns a visual representation of the agent tree with all decompositions and results.

### WebSocket Updates

```javascript
ws://localhost:8000/ws/tasks/{task_id}

// Message types:
{
  "type": "agent_created",
  "agent_id": "uuid",
  "parent_id": "uuid",
  "task": "subtask description"
}

{
  "type": "tool_called",
  "agent_id": "uuid",
  "tool": "web_search",
  "args": {...}
}

{
  "type": "agent_completed",
  "agent_id": "uuid",
  "result": {...},
  "evaluation": "accepted"
}
```

## Configuration

Key environment variables in `.env`:

```bash
# LLM Provider
MODEL_PROVIDER=anthropic
MODEL_NAME=claude-sonnet-4-5-20250929
ANTHROPIC_API_KEY=your_key_here

# Recursion Limits
MAX_TREE_DEPTH=10
MAX_AGENTS_PER_TASK=100
MAX_SUBAGENTS_PER_AGENT=5

# Execution Limits
AGENT_TIMEOUT_SECONDS=300
TOOL_TIMEOUT_SECONDS=30
MAX_TOOL_CALLS_PER_AGENT=20

# Code Execution
CODE_SANDBOX_ENABLED=true
CODE_EXECUTION_TIMEOUT=30
ALLOWED_LANGUAGES=python,javascript,bash

# Database
POSTGRES_DB=agi_memory
POSTGRES_USER=agi
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_URL=redis://redis:6379/0

# Safety
ENABLE_HUMAN_REVIEW=false
COST_LIMIT_PER_TASK=10.00
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

## Architecture Decisions

### Why Recursive Subagents?

1. **Natural Problem Decomposition**: Mirrors how humans break down complex problems
2. **Parallelization**: Subagents can run concurrently
3. **Specialization**: Each agent focuses on one specific subtask
4. **Scalability**: Tree can grow dynamically based on problem complexity
5. **Fault Isolation**: Failed agents don't crash the entire tree
6. **Quality Control**: Parent agents ensure subagent outputs meet standards

### Why Accept/Reject?

1. **Quality Assurance**: Ensures solutions meet requirements
2. **Iterative Improvement**: Agents learn from feedback
3. **Error Recovery**: Failed attempts can be revised
4. **Knowledge Refinement**: Rejection reasons improve future performance

### Tool Design Philosophy

Each tool serves a specific cognitive function:

- **Web Search**: External knowledge acquisition
- **Database Query**: Internal memory recall
- **Code Execution**: Hypothesis testing and validation
- **Create Subagent**: Cognitive offloading and delegation
- **Store Data**: Learning and knowledge accumulation

## Safety Mechanisms

1. **Recursion Limits**: Maximum tree depth and agent count
2. **Timeout Controls**: Per-agent and per-task timeouts
3. **Sandboxed Execution**: Isolated code execution environment
4. **Cost Tracking**: LLM API call cost monitoring
5. **Audit Logging**: Complete trace of all decisions
6. **Human Review**: Optional approval gates for critical tasks
7. **Resource Quotas**: CPU, memory, and network limits

## Example: Complex Task Execution

**Task**: "Build a sentiment analysis API"

```
Root Agent (Task: Build sentiment analysis API)
├─ Evaluates: This is complex, needs decomposition
├─ Creates 3 subagents:
│
├── Agent 1.1 (Task: Research sentiment analysis approaches)
│   ├─ Uses: web_search("best sentiment analysis models 2025")
│   ├─ Uses: db_query("past sentiment analysis projects")
│   ├─ Returns: "Use transformer-based model (BERT/RoBERTa)"
│   └─ Parent: ACCEPT ✓
│
├── Agent 1.2 (Task: Design API architecture)
│   ├─ Uses: web_search("FastAPI best practices")
│   ├─ Creates subagents:
│   │   ├── Agent 1.2.1: Design endpoints
│   │   ├── Agent 1.2.2: Design data models
│   │   └── Agent 1.2.3: Design error handling
│   ├─ Synthesizes: Complete API specification
│   └─ Parent: ACCEPT ✓
│
└── Agent 1.3 (Task: Implement the API)
    ├─ Creates subagents:
    │   ├── Agent 1.3.1: Model integration
    │   │   ├─ Uses: web_search("huggingface transformers API")
    │   │   ├─ Uses: execute_code(test_model_code)
    │   │   └─ Returns: Model integration code
    │   │
    │   ├── Agent 1.3.2: API endpoints
    │   │   ├─ Uses: execute_code(endpoint_code)
    │   │   └─ Returns: FastAPI endpoint code
    │   │
    │   └── Agent 1.3.3: Testing
    │       ├─ Uses: execute_code(test_suite)
    │       └─ Returns: Test results
    │
    ├─ Synthesizes: Complete implementation
    ├─ Parent evaluates: "Missing error handling"
    ├─ Parent: REJECT ✗ (Feedback: "Add proper error handling")
    ├─ Revises implementation
    └─ Parent: ACCEPT ✓

Root Agent synthesizes all results:
└─ Final output: Complete sentiment analysis API with docs
   ├─ Stores: store_data(solution, "completed_projects")
   └─ Returns: Success with implementation and insights
```

## Development

### Project Structure

```
agi/
├── docker-compose.yml
├── .env.example
├── mind/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
│       ├── main.py              # FastAPI server
│       ├── agent.py             # Core Agent class
│       ├── orchestrator.py      # Agent tree management
│       ├── evaluator.py         # Accept/reject logic
│       ├── tools/
│       │   ├── web_search.py
│       │   ├── database.py
│       │   ├── code_executor.py
│       │   ├── subagent.py
│       │   └── storage.py
│       └── models/
│           ├── task.py
│           ├── agent_tree.py
│           └── execution.py
└── database/
    └── init/
        └── 01_init_db.sql       # Agent tree schema
```

### Running Tests

```bash
# Test agent creation and execution
curl -X POST http://localhost:8000/test/simple \
  -d '{"task": "What is 2+2?"}'

# Test recursive decomposition
curl -X POST http://localhost:8000/test/recursive \
  -d '{"task": "Calculate fibonacci(10)"}'

# Test tool usage
curl -X POST http://localhost:8000/test/tools \
  -d '{"task": "Search for Python best practices"}'
```

## Roadmap

- [x] Core recursive agent architecture
- [x] Docker orchestration
- [ ] Agent class implementation
- [ ] Tool system (5 tools)
- [ ] Accept/reject evaluator
- [ ] Database schema for agent trees
- [ ] WebSocket real-time updates
- [ ] Tree visualization
- [ ] Cost tracking and limits
- [ ] Advanced synthesis strategies
- [ ] Multi-agent parallelization
- [ ] Learning from past executions
- [ ] Agent specialization
- [ ] Meta-learning capabilities

## License

MIT License - See LICENSE file for details

## Acknowledgments

Inspired by:
- Recursive task decomposition in AI planning
- Tree-of-Thought reasoning
- Multi-agent systems research
- AutoGPT and similar autonomous agents

Built with:
- Anthropic Claude for agent reasoning
- FastAPI for the orchestration server
- PostgreSQL + pgvector for memory
- Docker for containerization

---

**Note**: This is an experimental AGI platform exploring recursive subagent architectures for complex problem-solving.
