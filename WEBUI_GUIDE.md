# Web UI Guide - Real-time Thinking Visualization

Complete guide for the AGI Platform Web UI with real-time visualization of the recursive thinking process.

## 🎉 What Was Built

A complete real-time web UI that visualizes:
- **Thinking Tree**: Interactive tree diagram showing agent hierarchy
- **Thought Stream**: Live stream of agent reasoning
- **Memory Browser**: Search and browse stored memories
- **Real-time Updates**: WebSocket-powered live updates

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    User Browser                     │
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │         React Frontend (port 3000)          │  │
│  │  - ThinkingTree (ReactFlow)                 │  │
│  │  - ThoughtStream                            │  │
│  │  - MemoryPanel                              │  │
│  │  - WebSocket client                         │  │
│  └───────────┬─────────────────────────────────┘  │
└──────────────┼─────────────────────────────────────┘
               │
        HTTP + WebSocket
               │
┌──────────────▼─────────────────────────────────────┐
│              Nginx (port 80)                       │
│  - Static file serving                             │
│  - API proxy (/api/* → backend)                    │
│  - WebSocket proxy (/ws/* → backend)               │
└──────────────┬─────────────────────────────────────┘
               │
┌──────────────▼─────────────────────────────────────┐
│         Backend (realtime_server.py)               │
│  - FastAPI with WebSocket support                  │
│  - Connection manager                              │
│  - Progress event broadcasting                     │
│  - RecursiveAgent with callbacks                   │
└────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Build and Start All Services

```bash
# Build everything
docker-compose -f docker-compose.full.yml build

# Start all services
docker-compose -f docker-compose.full.yml up -d

# View logs
docker-compose -f docker-compose.full.yml logs -f
```

### 2. Access the Web UI

Open your browser to: **http://localhost:3000**

### 3. Submit a Task

Enter a complex task in the input field:

```
Research quantum computing trends, analyze their impact on various industries, and predict future developments
```

Click "Send" or press Enter.

### 4. Watch the Magic

- **Thinking Tree Tab**: See agents spawning in real-time
- **Thought Stream Tab**: Watch reasoning unfold
- **Memories Tab**: Browse stored information

## Features

### 🌳 Thinking Tree Visualization

**What it shows:**
- Agent hierarchy (parent-child relationships)
- Current status of each agent (thinking, executing, completed)
- Task description for each agent
- Real-time updates as agents are created

**Status Colors:**
- 🟡 **Yellow/Orange**: Thinking or executing
- 🔵 **Blue**: Currently executing tools
- 🟣 **Purple**: Evaluating results
- 🟢 **Green**: Completed successfully
- 🔴 **Red**: Failed or error

**Features:**
- Zoom and pan
- Mini-map for navigation
- Auto-layout with depth indication
- Animated connections

### 💭 Thought Stream

**What it shows:**
- Real-time stream of agent thoughts
- Thought types (analysis, planning, evaluation, execution)
- Timestamps
- Auto-scrolling to latest

**Thought Types:**
- 🧠 **Analysis**: Deep thinking about the task
- 💡 **Planning**: Decomposition strategy
- ✅ **Evaluation**: Result assessment
- ⚙️ **Execution**: Tool usage and actions

### 🗄️ Memory Browser

**What it shows:**
- All stored memories
- Search with semantic similarity
- Relevance scores
- Metadata tags

**Features:**
- Search by keyword or question
- Sort by relevance
- Filter by metadata
- View timestamps

## WebSocket Events

The frontend receives real-time events:

### Agent Events
```json
{
  "type": "agent_created",
  "agent_id": "uuid",
  "task": "Research quantum computing",
  "depth": 1,
  "parent_id": "parent-uuid",
  "timestamp": "2025-01-08T..."
}
```

```json
{
  "type": "agent_status",
  "agent_id": "uuid",
  "status": "thinking" | "executing" | "completed" | "failed",
  "timestamp": "..."
}
```

### Thought Events
```json
{
  "type": "thought",
  "agent_id": "uuid",
  "thought": "Task appears complex, will decompose into 3 subtasks",
  "thought_type": "analysis" | "planning" | "evaluation" | "execution",
  "timestamp": "..."
}
```

### Tool Events
```json
{
  "type": "tool_call",
  "agent_id": "uuid",
  "tool_name": "web_search",
  "arguments": {"query": "quantum computing 2024"},
  "timestamp": "..."
}
```

### Evaluation Events
```json
{
  "type": "evaluation",
  "agent_id": "uuid",
  "result": "accept" | "reject" | "needs_refinement",
  "reasoning": "Result meets requirements",
  "timestamp": "..."
}
```

## API Endpoints

### Execute Task
```bash
POST http://localhost:3000/execute
Content-Type: application/json

{
  "task": "Your complex task here",
  "max_depth": 5,
  "max_iterations": 3,
  "store_in_memory": true
}

# Response:
{
  "execution_id": "uuid",
  "message": "Task execution started. Connect to /ws/{execution_id}..."
}
```

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:3000/ws/{execution_id}');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message.type, message);
};
```

### Get Memories
```bash
GET http://localhost:3000/memories?query=quantum&limit=10
```

### Search Memories
```bash
GET http://localhost:3000/memories?query=what+did+we+learn
```

## Configuration

### Environment Variables

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
WEB_PORT=3000
MEMORY_COLLECTION_NAME=agi_memories
```

### Frontend Configuration

Edit `frontend/package.json`:
```json
{
  "proxy": "http://backend:8000"
}
```

### Nginx Configuration

Edit `frontend/nginx.conf` to change routing or add features.

## Development Mode

### Run Frontend Locally

```bash
cd frontend
npm install
npm start
```

Frontend will run on http://localhost:3000 with hot-reload.

### Run Backend Locally

```bash
# Terminal 1: Backend
python -m uvicorn src.server.realtime_server:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm start
```

## Docker Services

### Backend Service

```yaml
backend:
  build: .
  ports: []  # Internal only
  command: python -m uvicorn src.server.realtime_server:app --host 0.0.0.0 --port 8000
```

### Frontend Service

```yaml
frontend:
  build: ./frontend
  ports:
    - "3000:80"
  depends_on:
    - backend
```

## Customization

### Change Tree Layout

Edit `frontend/src/components/ThinkingTree.js`:
```javascript
const newNode = {
  position: {
    x: customX,  // Your custom X position
    y: customY,  // Your custom Y position
  },
  // ...
};
```

### Add Custom Thought Types

Edit `frontend/src/components/ThoughtStream.js`:
```javascript
const ThoughtIcon = ({ type }) => {
  const icons = {
    analysis: <Brain />,
    custom: <YourIcon />,  // Add new type
    // ...
  };
};
```

### Customize Colors

Edit `frontend/src/index.css`:
```css
.react-flow__node.thinking {
  border-color: #your-color;
}
```

## Troubleshooting

### WebSocket Connection Fails

**Problem**: Frontend can't connect to WebSocket

**Solutions**:
1. Check backend is running: `curl http://localhost:8000/health`
2. Check WebSocket URL in browser console
3. Verify nginx proxy configuration
4. Check firewall rules

### Tree Not Updating

**Problem**: Tree doesn't show new agents

**Solutions**:
1. Check browser console for WebSocket messages
2. Verify execution_id is correct
3. Check backend logs for event emission
4. Refresh the page

### Frontend Build Fails

**Problem**: Docker build fails for frontend

**Solutions**:
1. Check `frontend/package.json` syntax
2. Verify Node version (18+)
3. Clear npm cache: `npm cache clean --force`
4. Check `.dockerignore` doesn't exclude needed files

### Memories Not Loading

**Problem**: Memory panel shows no results

**Solutions**:
1. Check backend connection: `curl http://localhost:8000/memories`
2. Verify ChromaDB volume is mounted
3. Check backend logs for errors
4. Try without search query first

## Performance Optimization

### Reduce WebSocket Traffic

Throttle updates in `useWebSocket.js`:
```javascript
const throttledUpdate = useCallback(
  throttle((message) => {
    setMessages(prev => [...prev, message]);
  }, 100),  // 100ms throttle
  []
);
```

### Limit Tree Nodes

Set max depth to prevent huge trees:
```javascript
// TaskInput.js
max_depth: 3,  // Lower depth = fewer nodes
```

### Paginate Memories

```javascript
// MemoryPanel.js
const [page, setPage] = useState(0);
const limit = 20;
```

## Production Deployment

### Security

1. **Enable HTTPS**:
```nginx
server {
  listen 443 ssl;
  ssl_certificate /path/to/cert.pem;
  ssl_certificate_key /path/to/key.pem;
}
```

2. **Add Authentication**:
```javascript
// Add auth middleware to backend
// Add login page to frontend
```

3. **CORS Configuration**:
```python
# realtime_server.py
allow_origins=["https://yourdomain.com"]
```

### Scaling

1. **Multiple Backend Instances**:
```yaml
backend:
  deploy:
    replicas: 3
```

2. **Load Balancer**:
```yaml
nginx:
  # Configure upstream backend pool
```

3. **Redis for WebSocket State**:
```yaml
redis:
  image: redis:alpine
```

## Examples

### Example 1: Simple Task

**Input**: "Calculate factorial of 10"

**Expected Tree**:
```
Root Agent
  └─ Direct execution (no decomposition)
```

**Thoughts**:
- "Task is simple, executing directly"
- "Using execute_python tool"

### Example 2: Complex Research

**Input**: "Research top 3 AI companies, analyze strategies, predict winner"

**Expected Tree**:
```
Root Agent
  ├─ Research Agent 1 (Company research)
  │   ├─ Google AI
  │   ├─ OpenAI
  │   └─ Anthropic
  ├─ Analysis Agent 2 (Strategy analysis)
  └─ Prediction Agent 3 (Future prediction)
```

**Thoughts**:
- [ANALYSIS] "Complex multi-part task requiring decomposition"
- [PLANNING] "Breaking into 3 subtasks: research, analyze, predict"
- [EXECUTION] "Spawning research sub-agent"
- [EVALUATION] "Research results acceptable"

## Summary

The Web UI provides complete visibility into the recursive AGI thinking process:

✅ **Real-time visualization** of agent hierarchy
✅ **Live thought streaming** as agents reason
✅ **Memory browser** for persistent knowledge
✅ **WebSocket updates** for immediate feedback
✅ **Interactive tree** with zoom and pan
✅ **Multi-tab interface** for different views
✅ **Dockerized deployment** with one command

**Start now**: `docker-compose -f docker-compose.full.yml up -d`

**Access**: http://localhost:3000

**Watch your AI think in real-time! 🧠✨**
