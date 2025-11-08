# Migration Guide: Original → Recursive Architecture

Guide for understanding and switching between the two AGI agent architectures.

## Overview

The platform now supports **two architectures**:

1. **Original Agent** (`src/server/main.py`)
   - Simple, linear task execution
   - Basic tool calling
   - Memory integration
   - Best for: Simple queries, direct interactions

2. **Recursive Agent** (`src/server/recursive_main.py`) ← **Default**
   - Hierarchical task decomposition
   - Sub-agent spawning
   - Evaluation & refinement loops
   - Ultrathink analysis
   - Best for: Complex, multi-step problems

## Quick Comparison

| Feature | Original | Recursive |
|---------|----------|-----------|
| **Task Decomposition** | No | Yes (automatic) |
| **Sub-agents** | No | Yes (recursive) |
| **Evaluation Loop** | No | Yes (accept/reject) |
| **Ultrathink** | No | Yes |
| **Tools** | 1 (add_memory) | 5 (web, memory, code, storage, subagent) |
| **Execution Tree** | No | Yes (full trace) |
| **Refinement** | No | Yes (iterative) |
| **Complexity** | Simple | Advanced |
| **Latency** | Low (~2-5s) | Higher (~5-20s depending on depth) |
| **API Calls** | 1-3 per request | 3-15 per request (varies with depth) |

## Architecture Differences

### Original Architecture

```
User Request
     ↓
Single Agent
     ↓
Memory Retrieval
     ↓
Tool Execution (optional)
     ↓
Response
```

### Recursive Architecture

```
User Request
     ↓
Root Agent (Ultrathink)
     ├─ Subtask Analysis
     ├─ Sub-agent 1 → Execute → Evaluate
     ├─ Sub-agent 2 → Execute → Evaluate
     └─ Sub-agent 3 → Execute → Evaluate
          ├─ May spawn more sub-agents
          └─ Recursive evaluation
     ↓
Synthesis
     ↓
Response
```

## Switching Between Architectures

### Method 1: Docker CMD Override

Edit `docker-compose.yml`:

```yaml
services:
  agi-platform:
    # ... other config ...
    command: >
      python -m uvicorn src.server.main:app  # Original
      # OR
      python -m uvicorn src.server.recursive_main:app  # Recursive (default)
      --host 0.0.0.0 --port 8000
```

### Method 2: Dockerfile Modification

Edit `Dockerfile` line 75:

```dockerfile
# Original agent:
CMD ["python", "-m", "uvicorn", "src.server.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Recursive agent (default):
CMD ["python", "-m", "uvicorn", "src.server.recursive_main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Then rebuild:
```bash
make build
make up
```

### Method 3: Direct Python Execution

```bash
# Run original server
python -m uvicorn src.server.main:app --host 0.0.0.0 --port 8000

# Run recursive server
python -m uvicorn src.server.recursive_main:app --host 0.0.0.0 --port 8000
```

## API Endpoint Changes

### Original Agent Endpoints

```bash
POST /chat              # Chat with agent
POST /memory           # Add memory
POST /memory/search    # Search memories
GET  /tools            # List tools
```

### Recursive Agent Endpoints

```bash
POST /execute          # Execute task with recursive agents
GET  /tree/{agent_id}  # Get execution tree
POST /memory/search    # Search memories
POST /memory/store     # Store data
GET  /tools            # List tools (5 core tools)
```

## Request Format Changes

### Original Agent

```json
// POST /chat
{
    "message": "Your message",
    "conversation_history": [...],
    "store_in_memory": true
}
```

### Recursive Agent

```json
// POST /execute
{
    "task": "Your task",
    "max_depth": 5,
    "max_iterations": 3,
    "store_in_memory": true
}
```

## Response Format Changes

### Original Agent Response

```json
{
    "response": "Agent's answer",
    "tool_calls": [...],
    "memories_used": [...],
    "metadata": {...}
}
```

### Recursive Agent Response

```json
{
    "agent_id": "root-agent-uuid",
    "task": "Original task",
    "output": "Final synthesized answer",
    "thoughts": "Complete reasoning trace",
    "execution_tree": {
        "agent-1": {"task": "...", "children": [...], "status": "..."},
        "agent-2": {...}
    },
    "tool_calls": [...],
    "status": "completed"
}
```

## Code Migration Examples

### Example 1: Simple Chat → Task Execution

**Before (Original):**
```python
from src.agent.core import AGIAgent

agent = AGIAgent(...)
result = agent.process_message("What is 5 + 3?")
print(result.content)
```

**After (Recursive):**
```python
from src.agent.recursive_agent import RecursiveAgent

agent = RecursiveAgent(...)
result = agent.execute_task("What is 5 + 3?")
print(result.output)  # Note: .output instead of .content
```

### Example 2: Tool Usage

**Before (Original):**
```python
# Tools registered manually
tool_registry = ToolRegistry()
tool_registry.register_tool(...)
```

**After (Recursive):**
```python
# Enhanced tools included automatically
from src.agent.enhanced_tools import create_enhanced_registry

tool_registry = create_enhanced_registry(memory_store)
# Already includes: web_search, search_memory, store_data,
#                   execute_python, create_subagent
```

### Example 3: API Calls

**Before (Original):**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "store_in_memory": false}'
```

**After (Recursive):**
```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "Hello", "max_depth": 3, "store_in_memory": false}'
```

## When to Use Each Architecture

### Use Original Agent When:

- ✓ Simple, single-step queries
- ✓ Direct Q&A conversations
- ✓ Low latency requirements
- ✓ Cost-sensitive applications
- ✓ Straightforward tool execution
- ✓ Basic memory retrieval

**Example tasks:**
- "What's the weather?"
- "Calculate 42 * 17"
- "What did we discuss earlier?"
- "Store this information: ..."

### Use Recursive Agent When:

- ✓ Complex, multi-step problems
- ✓ Research and analysis tasks
- ✓ Problems requiring decomposition
- ✓ Need for validation/refinement
- ✓ Tasks with subtask dependencies
- ✓ Want execution traceability

**Example tasks:**
- "Research quantum computing, analyze trends, and predict future developments"
- "Calculate statistics for prime numbers under 1000 and visualize distribution"
- "Compare 3 programming languages for web development with pros/cons"
- "Analyze this dataset, identify patterns, and generate insights"

## Feature Availability

| Feature | Original | Recursive |
|---------|----------|-----------|
| Basic chat | ✓ | ✓ |
| Memory operations | ✓ | ✓ |
| Web search | ✗ | ✓ |
| Code execution | ✗ | ✓ |
| Task decomposition | ✗ | ✓ |
| Sub-agents | ✗ | ✓ |
| Evaluation loop | ✗ | ✓ |
| Execution tree | ✗ | ✓ |
| Ultrathink | ✗ | ✓ |
| Conversation history | ✓ | ✗ (use tasks) |
| Streaming | ✓ (in API) | ✗ (future) |

## Performance Implications

### Original Agent

- **Average latency**: 2-5 seconds
- **API calls**: 1-3 per request
- **Cost**: Low
- **Memory**: ~500MB-1GB
- **CPU**: Low

### Recursive Agent

- **Average latency**: 5-20 seconds (varies with depth)
- **API calls**: 3-15 per request (depth dependent)
- **Cost**: Medium-High (2-5x original)
- **Memory**: ~1-2GB
- **CPU**: Medium

## Gradual Migration Strategy

### Phase 1: Run Both (Recommended)

Run two separate instances:

```yaml
# docker-compose.yml
services:
  agi-original:
    build: .
    command: python -m uvicorn src.server.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"

  agi-recursive:
    build: .
    command: python -m uvicorn src.server.recursive_main:app --host 0.0.0.0 --port 8001
    ports:
      - "8001:8000"
```

Route requests based on complexity:
- Simple queries → Port 8000 (original)
- Complex tasks → Port 8001 (recursive)

### Phase 2: Test & Compare

```bash
# Test original
curl -X POST http://localhost:8000/chat \
  -d '{"message": "Test task"}'

# Test recursive
curl -X POST http://localhost:8001/execute \
  -d '{"task": "Test task"}'

# Compare results, latency, cost
```

### Phase 3: Full Migration

Once comfortable with recursive architecture:

```bash
# Switch to recursive only
docker-compose down
# Edit docker-compose.yml to use recursive_main
make build && make up
```

## Troubleshooting

### Issue: Recursive agent too slow

**Solution:**
- Reduce `max_depth` (try 2-3 instead of 5)
- Reduce `max_iterations` (try 1-2)
- Use original agent for simple tasks

### Issue: Too many API calls

**Solution:**
- Set stricter depth limits
- Use original agent for simple queries
- Implement caching for repeated tasks

### Issue: Poor task decomposition

**Solution:**
- Make tasks more specific
- Add constraints in request
- Adjust task description clarity

### Issue: Want old /chat endpoint

**Solution:**
- Run both servers (see Phase 1 above)
- Or create adapter endpoint in recursive_main.py

## Backward Compatibility

The recursive architecture is **not backward compatible** with the original `/chat` endpoint. However:

1. **Both servers share**:
   - Same memory store
   - Same API client
   - Same database

2. **Can run simultaneously**:
   - Original on port 8000
   - Recursive on port 8001

3. **Migration path**:
   - Gradual transition
   - A/B testing
   - Feature flagging

## Configuration

### Original Agent Config

```bash
# .env
ANTHROPIC_API_KEY=...
MAX_MEMORY_RESULTS=5
MEMORY_RELEVANCE_THRESHOLD=0.7
```

### Recursive Agent Config

```bash
# .env (same as above, plus:)
MAX_RECURSION_DEPTH=5
MAX_REFINEMENT_ITERATIONS=3
MAX_SUBAGENTS_PER_TASK=5
```

## Summary

| Decision Point | Original | Recursive |
|----------------|----------|-----------|
| **Task complexity** | Simple | Complex |
| **Speed priority** | High | Medium |
| **Cost priority** | Low cost | Higher cost OK |
| **Need decomposition** | No | Yes |
| **Need validation** | No | Yes |
| **Traceability** | Basic | Full tree |

## Support

- **Original Agent**: See `README.md` and `example_usage.py`
- **Recursive Agent**: See `RECURSIVE_ARCHITECTURE.md` and `example_recursive_usage.py`
- **Both**: See `DOCKER.md` for deployment

---

**Default**: The platform now uses the **Recursive Agent** by default for its advanced capabilities. Switch to the original agent for simple use cases.
