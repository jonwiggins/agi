# Quick Reference - Recursive AGI Platform

## 🚀 Start in 30 Seconds

```bash
make setup              # Create .env
# Edit .env: ANTHROPIC_API_KEY=sk-ant-...
make build && make up   # Build and start
```

Access: http://localhost:8000/docs

## 📡 Key Endpoints

### Execute Complex Task (Recursive)
```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Research quantum computing trends and predict future",
    "max_depth": 5,
    "max_iterations": 3,
    "store_in_memory": true
  }'
```

### Get Execution Tree
```bash
curl http://localhost:8000/tree/{agent_id}
```

### List Tools
```bash
curl http://localhost:8000/tools
# Returns: web_search, search_memory, store_data, execute_python, create_subagent
```

## 🛠️ 5 Core Tools

| Tool | Purpose | Example |
|------|---------|---------|
| `web_search` | Internet search | Research latest AI news |
| `search_memory` | Find stored info | What did we discuss? |
| `store_data` | Save information | Remember this fact |
| `execute_python` | Run code | Calculate primes |
| `create_subagent` | Delegate task | Spawn helper agent |

## 🧠 How It Works

```
Your Task
    ↓
Ultrathink (analyze)
    ↓
Decompose? ─No→ Execute directly
    ↓ Yes
Spawn sub-agents
    ├─ Agent 1 → Evaluate → Accept/Reject
    ├─ Agent 2 → Evaluate → Accept/Reject
    └─ Agent 3 → Evaluate → Accept/Reject
         ↓
Synthesize results
    ↓
Final answer + tree
```

## 🎯 When to Use What

### Use Recursive Agent (Default)
- ✅ "Research X, analyze Y, predict Z"
- ✅ "Calculate stats and visualize"
- ✅ "Compare A, B, C with pros/cons"
- ✅ Multi-step, complex problems

### Use Original Agent
- ✅ "What's 5 + 3?"
- ✅ "Hello, how are you?"
- ✅ Simple Q&A
- ✅ Single-step tasks

**Switch**: Edit `docker-compose.yml` → `command: python -m uvicorn src.server.main:app...`

## 🐍 Python Usage

```python
from src.agent.recursive_agent import RecursiveAgent
from src.agent.enhanced_tools import create_enhanced_registry

# Setup
agent = RecursiveAgent(...)

# Execute
result = agent.execute_task("Complex task here")

# Results
print(result.output)           # Final answer
print(result.thoughts)         # Reasoning
print(result.tool_calls)       # Tools used
tree = agent.get_execution_tree()  # Full tree
```

## ⚙️ Configuration

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...    # Required
MAX_RECURSION_DEPTH=5           # Max levels (default: 5)
MAX_REFINEMENT_ITERATIONS=3     # Max retries (default: 3)
MAX_SUBAGENTS_PER_TASK=5        # Max children (default: 5)
```

## 🐳 Docker Commands

```bash
make setup      # First-time setup
make build      # Build image
make up         # Start (detached)
make logs       # View logs
make status     # Check status
make test-docker # Run tests
make shell      # Open shell
make down       # Stop
make clean      # Remove all
```

## 📊 Performance

| Metric | Value |
|--------|-------|
| **Simple task** | 5-10s |
| **Medium task** | 10-20s |
| **Complex task** | 20-40s |
| **API calls** | 3-30 per request |
| **Memory** | 1-2GB |

## 🔍 Debug

### View execution tree
```python
tree = agent.get_execution_tree()
for aid, node in tree.items():
    print(f"{node['task']} - {node['status']}")
```

### View agent thoughts
```python
thoughts = agent.get_agent_thoughts(agent_id)
for t in thoughts:
    print(f"[{t.thought_type}] {t.thought}")
```

### Check logs
```bash
make logs
# Or
docker logs agi-platform
```

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Main overview |
| `RECURSIVE_ARCHITECTURE.md` | Complete guide |
| `MIGRATION_GUIDE.md` | Switch between architectures |
| `RECURSIVE_SUMMARY.md` | What was built |
| `QUICK_REFERENCE.md` | This file |
| `DOCKER.md` | Docker details |

## 🆘 Common Issues

### Too slow
- Reduce `max_depth` to 2-3
- Reduce `max_iterations` to 1-2
- Use original agent for simple tasks

### Too many API calls
- Set lower `max_depth`
- Simplify task description
- Use original agent

### Poor decomposition
- Be more specific in task
- Add constraints
- Check task complexity

## 💡 Examples

### Research Task
```json
{
  "task": "Research top 3 ML frameworks, compare features, recommend best for startups"
}
```

### Analysis Task
```json
{
  "task": "Analyze Fibonacci sequence: generate first 50, find patterns, calculate ratios"
}
```

### Multi-step Task
```json
{
  "task": "1) Search for quantum computing news, 2) Summarize top 5 breakthroughs, 3) Predict 2025 trends"
}
```

## 🎓 Learn More

```bash
# Run examples
python example_recursive_usage.py

# Read architecture
cat RECURSIVE_ARCHITECTURE.md

# Migration guide
cat MIGRATION_GUIDE.md
```

## 🔗 URLs

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc
- **Health**: http://localhost:8000/health

## 🏁 Quick Test

```bash
# Start
make up

# Test
curl -X POST http://localhost:8000/execute \
  -d '{"task": "What is 5! (factorial)?"}'

# Should decompose, execute Python, return 120
```

---

**Need help?** → `make logs` or see full docs in RECURSIVE_ARCHITECTURE.md
