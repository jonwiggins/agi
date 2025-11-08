"""
Real-time AGI server with WebSocket support for live visualization.

This server extends the recursive agent with real-time progress tracking
for the web UI.
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os
import uuid
import asyncio
from contextlib import asynccontextmanager

from ..api.client import AnthropicClient
from ..memory.embeddings import EmbeddingGenerator
from ..memory.store import MemoryStore
from ..agent.recursive_agent import RecursiveAgent, AgentContext
from ..agent.enhanced_tools import create_enhanced_registry
from .websocket_server import connection_manager


# Pydantic models
class ExecuteTaskRequest(BaseModel):
    """Request to execute a task with real-time updates."""
    task: str = Field(..., description="The task to execute")
    max_depth: int = Field(default=5, description="Maximum recursion depth")
    max_iterations: int = Field(default=3, description="Maximum refinement iterations")
    store_in_memory: bool = Field(default=True, description="Store results in memory")


class ExecuteTaskResponse(BaseModel):
    """Response with execution ID for tracking."""
    execution_id: str = Field(..., description="Unique execution ID")
    message: str = Field(..., description="Status message")


class MemoryItem(BaseModel):
    """Memory item for display."""
    id: str
    content: str
    relevance: float
    metadata: Dict[str, Any]
    timestamp: str


class MemoriesResponse(BaseModel):
    """Response containing memories."""
    memories: List[MemoryItem]
    total: int


# Global state
agent: Optional[RecursiveAgent] = None
active_executions: Dict[str, Dict[str, Any]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    global agent
    agent = initialize_agent()
    yield
    # Cleanup
    active_executions.clear()


# Create FastAPI app
app = FastAPI(
    title="AGI Platform - Real-time API",
    description="Real-time recursive AGI with WebSocket visualization",
    version="0.3.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def initialize_agent() -> RecursiveAgent:
    """Initialize the recursive AGI agent."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    chroma_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma")
    collection_name = os.getenv("MEMORY_COLLECTION_NAME", "agi_memories")
    default_model = os.getenv("DEFAULT_MODEL", "claude-sonnet-4-5-20250929")

    # Initialize components
    embedding_generator = EmbeddingGenerator(api_key=api_key)
    memory_store = MemoryStore(
        persist_directory=chroma_dir,
        collection_name=collection_name,
        embedding_generator=embedding_generator,
    )
    api_client = AnthropicClient(api_key=api_key, default_model=default_model)
    tool_registry = create_enhanced_registry(memory_store=memory_store)

    return RecursiveAgent(
        api_client=api_client,
        memory_store=memory_store,
        tool_registry=tool_registry,
        max_depth=5,
        max_iterations=3,
        max_subagents=5,
    )


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AGI Platform - Real-time API",
        "version": "0.3.0",
        "features": ["real-time-websocket", "tree-visualization", "memory-display"],
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "websocket_ready": True}


@app.websocket("/ws/{execution_id}")
async def websocket_endpoint(websocket: WebSocket, execution_id: str):
    """WebSocket endpoint for real-time updates.

    Args:
        websocket: WebSocket connection
        execution_id: Execution ID to subscribe to
    """
    await connection_manager.connect(websocket, execution_id)

    try:
        # Keep connection alive
        while True:
            # Receive ping messages
            data = await websocket.receive_text()

            # Handle client messages (e.g., pause, resume)
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket, execution_id)


@app.post("/execute", response_model=ExecuteTaskResponse)
async def execute_task(request: ExecuteTaskRequest):
    """Execute a task with real-time WebSocket updates.

    Args:
        request: Task execution request

    Returns:
        Execution ID for WebSocket subscription
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    # Generate execution ID
    execution_id = str(uuid.uuid4())

    # Store execution info
    active_executions[execution_id] = {
        "task": request.task,
        "status": "started",
        "start_time": None,
    }

    # Execute in background
    asyncio.create_task(
        execute_task_with_updates(
            execution_id,
            request.task,
            request.max_depth,
            request.max_iterations,
            request.store_in_memory,
        )
    )

    return ExecuteTaskResponse(
        execution_id=execution_id,
        message="Task execution started. Connect to /ws/{execution_id} for real-time updates."
    )


async def execute_task_with_updates(
    execution_id: str,
    task: str,
    max_depth: int,
    max_iterations: int,
    store_in_memory: bool,
):
    """Execute task and send WebSocket updates.

    Args:
        execution_id: Execution ID
        task: Task to execute
        max_depth: Max depth
        max_iterations: Max iterations
        store_in_memory: Store in memory flag
    """
    try:
        # Update status
        active_executions[execution_id]["status"] = "running"

        # Set up agent with WebSocket callback
        agent.websocket_callback = lambda event_type, **kwargs: asyncio.create_task(
            handle_agent_event(execution_id, event_type, **kwargs)
        )

        # Execute task
        result = agent.execute_task(task)

        # Store in memory if requested
        if store_in_memory and result:
            agent.memory_store.add_memory(
                content=f"Task: {task}\n\nResult: {result.output}",
                metadata={
                    "type": "task_execution",
                    "execution_id": execution_id,
                    "status": result.status.value,
                }
            )

        # Send completion
        await connection_manager.send_completion(
            execution_id,
            result.agent_id if result else "unknown",
            result.output if result else "No output"
        )

        # Update status
        active_executions[execution_id]["status"] = "completed"
        active_executions[execution_id]["result"] = result

    except Exception as e:
        # Send error
        await connection_manager.send_error(execution_id, "root", str(e))
        active_executions[execution_id]["status"] = "error"
        active_executions[execution_id]["error"] = str(e)


async def handle_agent_event(execution_id: str, event_type: str, **kwargs):
    """Handle agent events and broadcast via WebSocket.

    Args:
        execution_id: Execution ID
        event_type: Type of event
        **kwargs: Event data
    """
    if event_type == "agent_created":
        await connection_manager.send_agent_created(
            execution_id,
            kwargs.get("agent_id"),
            kwargs.get("task"),
            kwargs.get("depth"),
            kwargs.get("parent_id"),
        )
    elif event_type == "status_change":
        await connection_manager.send_agent_status(
            execution_id,
            kwargs.get("agent_id"),
            kwargs.get("status"),
        )
    elif event_type == "thought":
        await connection_manager.send_thought(
            execution_id,
            kwargs.get("agent_id"),
            kwargs.get("thought"),
            kwargs.get("thought_type"),
        )
    elif event_type == "tool_call":
        await connection_manager.send_tool_call(
            execution_id,
            kwargs.get("agent_id"),
            kwargs.get("tool_name"),
            kwargs.get("arguments"),
        )
    elif event_type == "evaluation":
        await connection_manager.send_evaluation(
            execution_id,
            kwargs.get("agent_id"),
            kwargs.get("result"),
            kwargs.get("reasoning"),
        )


@app.get("/execution/{execution_id}")
async def get_execution_status(execution_id: str):
    """Get status of an execution.

    Args:
        execution_id: Execution ID

    Returns:
        Execution status and result
    """
    if execution_id not in active_executions:
        raise HTTPException(status_code=404, detail="Execution not found")

    execution = active_executions[execution_id]

    response = {
        "execution_id": execution_id,
        "task": execution["task"],
        "status": execution["status"],
    }

    if "result" in execution:
        result = execution["result"]
        response["output"] = result.output
        response["tree"] = agent.get_execution_tree() if agent else {}

    if "error" in execution:
        response["error"] = execution["error"]

    return response


@app.get("/memories", response_model=MemoriesResponse)
async def get_memories(
    query: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get memories with optional search.

    Args:
        query: Optional search query
        limit: Max results
        offset: Results offset

    Returns:
        List of memories
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        if query:
            # Search memories
            results = agent.memory_store.search_memories(query=query, n_results=limit)
        else:
            # Get all memories
            results = agent.memory_store.get_all_memories(limit=limit)

        memories = [
            MemoryItem(
                id=m.get("id", ""),
                content=m.get("content", ""),
                relevance=m.get("relevance", 1.0),
                metadata=m.get("metadata", {}),
                timestamp=m.get("metadata", {}).get("timestamp", ""),
            )
            for m in results[offset:offset + limit]
        ]

        return MemoriesResponse(
            memories=memories,
            total=len(results)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools")
async def list_tools():
    """List all available tools."""
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    tool_definitions = agent.tool_registry.get_tool_definitions()
    return {
        "tools": tool_definitions,
        "count": len(tool_definitions),
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(app, host=host, port=port)
