**# Recursive Sub-Agent Architecture**

Complete guide to the recursive AGI agent system with task decomposition, validation, and ultrathink.

## Overview

The Recursive AGI platform uses a hierarchical agent system where complex tasks are automatically decomposed into subtasks, delegated to specialized sub-agents, evaluated, and synthesized back up the chain.

### Key Concepts

**1. Recursive Decomposition**
- Complex tasks are analyzed ("ultrathink" phase)
- Broken down into manageable subtasks
- Sub-agents spawned to handle each piece
- Results synthesized at each level

**2. Evaluation Loop**
- Every sub-agent's output is evaluated
- Accept ✓ / Reject ✗ / Needs Refinement decisions
- Feedback provided for improvements
- Iterative refinement until acceptance

**3. Context Propagation**
- Each agent receives overall goal + specific task
- Parent context flows down the hierarchy
- Constraints accumulate through iterations

**4. Ultrathink Mode**
- Deep analysis before execution
- Identifies complexity and dependencies
- Plans decomposition strategy
- Anticipates potential issues

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│ User Request: "Complex Multi-step Task"                │
└──────────────────────┬──────────────────────────────────┘
                       ▼
        ┌──────────────────────────────┐
        │   Root Agent (Depth 0)       │
        │   - Ultrathink Analysis      │
        │   - Decomposition Decision   │
        └──────────┬───────────────────┘
                   │
        ┌──────────┴────────────┬──────────────────┐
        ▼                       ▼                  ▼
┌───────────────┐      ┌───────────────┐   ┌───────────────┐
│ Sub-Agent 1   │      │ Sub-Agent 2   │   │ Sub-Agent 3   │
│ (Depth 1)     │      │ (Depth 1)     │   │ (Depth 1)     │
│ Subtask A     │      │ Subtask B     │   │ Subtask C     │
└───────┬───────┘      └───────┬───────┘   └───────┬───────┘
        │                      │                    │
        ▼                      ▼                    ▼
  [Execute]            [May spawn more]        [Execute]
        │              sub-agents...                │
        │                      │                    │
        ▼                      ▼                    ▼
  [Evaluate]             [Evaluate]            [Evaluate]
        │                      │                    │
        ├─ Accept ✓            ├─ Reject ✗          ├─ Accept ✓
        │  Refine ↻            │  (retry)           │
        │                      │                    │
        └──────────┬───────────┴────────────────────┘
                   ▼
        ┌──────────────────────────────┐
        │   Synthesis & Combination    │
        │   - Integrate all results    │
        │   - Resolve dependencies     │
        │   - Generate final answer    │
        └──────────┬───────────────────┘
                   ▼
          Final Result to User
```

## Execution Flow

### Phase 1: Ultra-Think Analysis

```python
{
    "analysis": "Deep analysis of task complexity and requirements",
    "needs_decomposition": true/false,
    "reasoning": "Why this decision was made",
    "subtasks": [
        {
            "description": "Specific subtask",
            "rationale": "Why this subtask exists",
            "expected_output": "What we expect back",
            "dependencies": [0, 2]  # Depends on subtask 0 and 2
        }
    ],
    "potential_issues": ["issue1", "issue2"],
    "recommended_tools": ["web_search", "execute_python"]
}
```

### Phase 2: Execution Strategy

**If decomposition NOT needed:**
- Execute directly with available tools
- Return result immediately

**If decomposition needed:**
- Spawn sub-agents (one per subtask)
- Each sub-agent repeats the process recursively
- Collect and validate all results

### Phase 3: Evaluation & Validation

For each sub-agent result:

```python
{
    "result": "accept | reject | needs_refinement",
    "reasoning": "Detailed explanation",
    "suggested_changes": [
        "Be more specific about X",
        "Include data about Y"
    ],
    "additional_context": "Extra information for refinement"
}
```

**Evaluation outcomes:**
- **Accept** ✓: Result meets requirements, proceed
- **Reject** ✗: Try again with feedback (up to max iterations)
- **Needs Refinement**: Minor changes needed, iterate

### Phase 4: Synthesis

- Combine accepted results
- Resolve dependencies
- Generate coherent final answer
- Propagate up to parent agent

## Enhanced Tool System

Every agent has access to 5 core tools:

### 1. Web Search (`web_search`)

Search the internet for information:

```python
{
    "query": "latest quantum computing breakthroughs 2024",
    "num_results": 5
}
# Returns: titles, snippets, URLs
```

### 2. Memory Search (`search_memory`)

Semantic search through stored memories:

```python
{
    "query": "What did we learn about Fibonacci?",
    "n_results": 5
}
# Returns: relevant stored information
```

### 3. Data Storage (`store_data`)

Persist information for future use:

```python
{
    "content": "Important finding or result",
    "metadata_json": '{"category": "research", "topic": "quantum"}'
}
# Returns: memory_id
```

### 4. Python Execution (`execute_python`)

Run Python code in a sandbox:

```python
{
    "code": """
import math
result = sum(i**2 for i in range(1, 11))
print(f"Sum of squares: {result}")
    """,
    "timeout": 30
}
# Returns: stdout, stderr, return_code
```

### 5. Sub-Agent Creation (`create_subagent`)

Delegate a subtask to a new agent:

```python
{
    "subtask": "Calculate fibonacci numbers 1-20",
    "context": "Part of larger analysis task",
    "expected_output": "List of 20 fibonacci numbers with statistics"
}
# Returns: sub-agent's complete result
```

## Agent Context

Each agent receives comprehensive context:

```python
AgentContext(
    agent_id="uuid-here",
    task="Specific task for this agent",
    parent_context="What the parent agent was doing",
    overall_goal="The original user request",
    depth=2,  # How deep in the tree
    max_depth=5,  # Maximum allowed depth
    parent_agent_id="parent-uuid",
    constraints=["Must include sources", "Be concise"],
    available_tools=["web_search", "execute_python", ...]
)
```

## Configuration

### Agent Parameters

```python
RecursiveAgent(
    api_client=...,
    memory_store=...,
    tool_registry=...,
    max_depth=5,        # Maximum recursion depth
    max_iterations=3,   # Max refinement iterations per subtask
    max_subagents=5,    # Max sub-agents per parent
)
```

### Environment Variables

```bash
# Same as before, plus:
MAX_RECURSION_DEPTH=5
MAX_REFINEMENT_ITERATIONS=3
MAX_SUBAGENTS_PER_TASK=5
```

## API Endpoints

### Execute Task

```bash
POST /execute
```

Request:
```json
{
    "task": "Research quantum computing and write a summary",
    "max_depth": 5,
    "max_iterations": 3,
    "store_in_memory": true
}
```

Response:
```json
{
    "agent_id": "root-agent-uuid",
    "task": "Research quantum computing...",
    "output": "Comprehensive summary...",
    "thoughts": "Analysis and reasoning...",
    "execution_tree": {
        "agent-1": {
            "task": "...",
            "children": ["agent-2", "agent-3"],
            "status": "completed"
        }
    },
    "tool_calls": [...],
    "status": "completed"
}
```

### Get Execution Tree

```bash
GET /tree/{agent_id}
```

Returns complete tree with all thoughts and status.

### List Tools

```bash
GET /tools
```

Returns all available tools with descriptions.

## Example Usage

### Python API

```python
from src.agent.recursive_agent import RecursiveAgent

# Initialize agent (see example_recursive_usage.py)
agent = RecursiveAgent(...)

# Execute a complex task
result = agent.execute_task(
    "Research the top 3 AI breakthroughs in 2024, "
    "analyze their impact, and predict future trends"
)

print(result.output)
print(f"Used {len(result.tool_calls)} tools")

# View execution tree
tree = agent.get_execution_tree()
for agent_id, node in tree.items():
    print(f"{node['task']} - {node['status']}")

# View agent thoughts
thoughts = agent.get_agent_thoughts(result.agent_id)
for thought in thoughts:
    print(f"[{thought.thought_type}] {thought.thought}")
```

### REST API

```bash
# Execute task
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Calculate statistics for prime numbers under 100 and visualize the distribution",
    "max_depth": 4,
    "store_in_memory": true
  }'

# Get execution tree
curl http://localhost:8000/tree/{agent_id}

# List available tools
curl http://localhost:8000/tools
```

## Thought Types

Agents produce different types of thoughts:

- **analysis**: Deep thinking about the task
- **planning**: Decomposition and strategy decisions
- **execution**: Tool calls and actions taken
- **evaluation**: Assessment of sub-agent results
- **synthesis**: Combining results together

## Best Practices

### Task Design

✓ **Good tasks for recursive decomposition:**
- Multi-step research projects
- Complex calculations with dependencies
- Tasks requiring multiple data sources
- Problems with clear subtask boundaries

✗ **Tasks that don't need recursion:**
- Simple calculations
- Single API calls
- Direct fact lookups
- Already atomic operations

### Depth Management

- Start with `max_depth=3-5` for most tasks
- Deep trees (>5) can be slow
- Shallow trees (<3) may not decompose enough
- Monitor execution trees to optimize

### Iteration Control

- `max_iterations=2-3` is usually sufficient
- More iterations = more refinement but slower
- Set lower for time-sensitive tasks
- Set higher for quality-critical work

## Comparison: Original vs Recursive

| Aspect | Original Agent | Recursive Agent |
|--------|---------------|-----------------|
| **Task Handling** | Linear, single-agent | Hierarchical, multi-agent |
| **Complexity** | Simple tasks | Complex, multi-step tasks |
| **Tools** | Basic tools | Enhanced (5 core tools) |
| **Validation** | None | Evaluation loop with refinement |
| **Thinking** | Basic reasoning | Ultrathink analysis |
| **Scalability** | Limited | Recursive scaling |
| **Traceability** | Basic | Full execution tree |

## Docker Deployment

### Use Recursive Server

Update `Dockerfile` CMD:

```dockerfile
CMD ["python", "-m", "uvicorn", "src.server.recursive_main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Or set in `docker-compose.yml`:

```yaml
command: python -m uvicorn src.server.recursive_main:app --host 0.0.0.0 --port 8000
```

### Build and Run

```bash
# Rebuild with new architecture
make build

# Start
make up

# Test recursive execution
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "Analyze the first 50 prime numbers"}'
```

## Performance Considerations

### Latency

- Each depth level adds ~3-5 seconds
- Parallel sub-agents help (when independent)
- Tool calls add variable latency
- Total time: O(depth × iterations)

### Cost

- More agents = more API calls
- Evaluation adds extra calls
- Ultrathink adds analysis calls
- Estimate: 2-5x cost vs simple agent

### Optimization

- Cache frequent tool results
- Limit depth for time-sensitive tasks
- Use lower max_iterations when acceptable
- Consider task complexity before decomposing

## Troubleshooting

### Infinite Recursion

**Problem**: Agent keeps spawning sub-agents
**Solution**: Check max_depth, improve task specificity

### Poor Decomposition

**Problem**: Subtasks don't make sense
**Solution**: Improve task description, add constraints

### Evaluation Failures

**Problem**: All results rejected
**Solution**: Adjust expected_output, lower standards

### Tool Errors

**Problem**: Web search or code execution fails
**Solution**: Check network, validate code syntax

## Advanced Features

### Custom Tools

Add domain-specific tools:

```python
from src.agent.tools import Tool, ToolParameter, ToolParameterType

def custom_tool(param: str) -> dict:
    # Your tool logic
    return {"result": "data"}

tool_registry.register_tool_direct(Tool(
    name="custom_tool",
    description="What it does",
    parameters=[...],
    function=custom_tool,
))
```

### Custom Evaluation

Override `_evaluate_result` for domain-specific validation:

```python
class CustomRecursiveAgent(RecursiveAgent):
    def _evaluate_result(self, result, expected_output, context):
        # Custom evaluation logic
        return EvaluationFeedback(...)
```

## Future Enhancements

- [ ] Parallel sub-agent execution
- [ ] Agent communication protocols
- [ ] Shared working memory
- [ ] Learning from past evaluations
- [ ] Cost optimization strategies
- [ ] Real-time progress streaming
- [ ] Visual execution tree UI
- [ ] Agent collaboration patterns

---

**The recursive architecture enables solving complex, multi-step problems through intelligent decomposition, delegation, and validation.**
