"""
AGI Mind - Recursive Subagent Architecture API Server
"""

import os
import asyncio
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog

from src.agent import Agent

# Initialize structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="AGI Mind - Recursive Subagent API",
    description="Recursive task solving through dynamic subagent decomposition",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task storage (in production, use database)
tasks_db: Dict[UUID, Dict[str, Any]] = {}

# ==========================================
# Data Models
# ==========================================

class TaskCreate(BaseModel):
    """Model for creating a new task"""
    task: str = Field(..., min_length=1, max_length=10000, description="The task to solve")
    context: Dict[str, Any] = Field(default={}, description="Additional context")
    max_depth: int = Field(default=5, ge=1, le=10, description="Maximum recursion depth")
    max_agents: int = Field(default=50, ge=1, le=100, description="Maximum total agents")
    timeout: int = Field(default=1800, ge=60, le=7200, description="Timeout in seconds")

class TaskResponse(BaseModel):
    """Model for task response"""
    task_id: str
    status: str
    created_at: str
    agent_tree_id: Optional[str] = None

class TaskResult(BaseModel):
    """Model for task result"""
    task_id: str
    task: str
    status: str
    context: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    created_at: str
    completed_at: Optional[str] = None

# ==========================================
# API Endpoints
# ==========================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "architecture": "recursive_subagent"
    }

@app.post("/tasks", response_model=TaskResponse)
async def create_task(task_create: TaskCreate):
    """
    Submit a new task for recursive solving.
    
    The system will:
    1. Analyze the task complexity
    2. Decide whether to solve directly or decompose
    3. If decomposing, spawn subagents recursively
    4. Synthesize results back up the tree
    5. Return the final answer
    """
    task_id = uuid4()
    
    logger.info(
        "task_submitted",
        task_id=str(task_id),
        task=task_create.task[:100]
    )
    
    # Store task
    tasks_db[task_id] = {
        "id": task_id,
        "task": task_create.task,
        "context": task_create.context,
        "max_depth": task_create.max_depth,
        "max_agents": task_create.max_agents,
        "timeout": task_create.timeout,
        "status": "processing",
        "created_at": datetime.utcnow(),
        "result": None,
        "metrics": {}
    }
    
    # Start task processing in background
    asyncio.create_task(process_task(task_id))
    
    return TaskResponse(
        task_id=str(task_id),
        status="processing",
        created_at=tasks_db[task_id]["created_at"].isoformat(),
        agent_tree_id=str(uuid4())
    )

@app.get("/tasks", response_model=List[TaskResult])
async def list_tasks():
    """List all tasks"""
    results = []
    for tid, task_data in tasks_db.items():
        results.append(TaskResult(
            task_id=str(tid),
            task=task_data["task"],
            status=task_data["status"],
            context=task_data.get("context"),
            result=task_data.get("result"),
            metrics=task_data.get("metrics"),
            error=task_data.get("error"),
            created_at=task_data["created_at"].isoformat(),
            completed_at=task_data.get("completed_at").isoformat() if task_data.get("completed_at") else None
        ))

    # Sort by created_at descending (newest first)
    results.sort(key=lambda x: x.created_at, reverse=True)
    return results

@app.get("/tasks/{task_id}", response_model=TaskResult)
async def get_task(task_id: str):
    """Get task status and results"""
    try:
        tid = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    if tid not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = tasks_db[tid]

    return TaskResult(
        task_id=str(tid),
        task=task_data["task"],
        status=task_data["status"],
        context=task_data.get("context"),
        result=task_data.get("result"),
        metrics=task_data.get("metrics"),
        error=task_data.get("error"),
        created_at=task_data["created_at"].isoformat(),
        completed_at=task_data.get("completed_at").isoformat() if task_data.get("completed_at") else None
    )

@app.get("/tasks/{task_id}/tree")
async def get_task_tree(task_id: str):
    """
    Get visual representation of the agent tree.

    Returns the full tree structure showing:
    - All agents and their relationships
    - Task decompositions
    - Results at each level
    - Evaluation decisions
    """
    try:
        tid = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    if tid not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = tasks_db[tid]
    agent_tree = task_data.get("agent_tree")

    if not agent_tree:
        return {
            "task_id": task_id,
            "tree": {"nodes": [], "edges": []},
            "total_nodes": 0
        }

    # Build nodes and edges for visualization
    nodes = []
    edges = []

    def traverse_agents(agent_data, parent_id=None):
        """Recursively traverse agent tree and build nodes/edges"""
        agent_id = agent_data["agent_id"]

        nodes.append({
            "id": agent_id,
            "label": f"Agent {agent_id[:8]}",
            "task": agent_data["assigned_task"][:100] + "..." if len(agent_data["assigned_task"]) > 100 else agent_data["assigned_task"],
            "status": agent_data["status"],
            "depth": agent_data["depth"],
            "tool_calls": len(agent_data.get("tool_calls", []))
        })

        if parent_id:
            edges.append({"from": parent_id, "to": agent_id})

        for subagent in agent_data.get("subagents", []):
            traverse_agents(subagent, agent_id)

    traverse_agents(agent_tree)

    return {
        "task_id": task_id,
        "tree": {
            "nodes": nodes,
            "edges": edges
        },
        "total_nodes": len(nodes)
    }

@app.get("/tasks/{task_id}/agents/{agent_id}")
async def get_agent_details(task_id: str, agent_id: str):
    """
    Get details for a specific agent including tool calls.
    """
    try:
        tid = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    if tid not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = tasks_db[tid]
    agent_tree = task_data.get("agent_tree")

    if not agent_tree:
        raise HTTPException(status_code=404, detail="Agent tree not available")

    # Find agent in tree
    def find_agent(agent_data, target_id):
        """Recursively search for agent by ID"""
        if agent_data["agent_id"] == target_id:
            return agent_data
        for subagent in agent_data.get("subagents", []):
            found = find_agent(subagent, target_id)
            if found:
                return found
        return None

    agent_data = find_agent(agent_tree, agent_id)

    if not agent_data:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent_data

@app.websocket("/ws/tasks/{task_id}")
async def websocket_task_updates(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time task updates.
    
    Streams events like:
    - agent_created
    - tool_called
    - agent_completed
    - evaluation_result
    """
    await websocket.accept()
    
    logger.info("websocket_connected", task_id=task_id)
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "connected",
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # TODO: Stream real-time updates from task execution
        
        # Keep connection alive
        while True:
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        logger.info("websocket_disconnected", task_id=task_id)

@app.get("/stats")
async def get_stats():
    """Get system statistics including cost tracking"""
    total_tasks = len(tasks_db)
    completed = sum(1 for t in tasks_db.values() if t["status"] == "completed")
    processing = sum(1 for t in tasks_db.values() if t["status"] == "processing")
    failed = sum(1 for t in tasks_db.values() if t["status"] == "failed")

    # Calculate cost statistics
    total_cost = sum(
        t.get("metrics", {}).get("cost_usd", 0.0)
        for t in tasks_db.values()
    )

    avg_cost_per_task = total_cost / total_tasks if total_tasks > 0 else 0.0

    # Get most expensive task
    most_expensive = None
    if tasks_db:
        most_expensive_task = max(
            tasks_db.values(),
            key=lambda t: t.get("metrics", {}).get("cost_usd", 0.0),
            default=None
        )
        if most_expensive_task:
            most_expensive = {
                "task_id": str(most_expensive_task["id"]),
                "cost_usd": most_expensive_task.get("metrics", {}).get("cost_usd", 0.0),
                "description": most_expensive_task["task"][:100]
            }

    return {
        "tasks": {
            "total": total_tasks,
            "completed": completed,
            "processing": processing,
            "failed": failed
        },
        "costs": {
            "total_usd": round(total_cost, 4),
            "average_per_task_usd": round(avg_cost_per_task, 4),
            "most_expensive_task": most_expensive
        },
        "uptime_seconds": 0  # TODO: Track actual uptime
    }

# ==========================================
# Background Task Processing
# ==========================================

async def process_task(task_id: UUID):
    """
    Process a task using the recursive agent system.
    """
    task_data = tasks_db[task_id]
    
    try:
        # Create root agent
        root_agent = Agent(
            agent_id=uuid4(),
            task_id=task_id,
            assigned_task=task_data["task"],
            context=task_data["context"],
            parent_id=None,
            depth=0,
            max_depth=task_data["max_depth"],
            timeout_seconds=task_data["timeout"]
        )
        
        # Execute with timeout
        result = await asyncio.wait_for(
            root_agent.solve(),
            timeout=task_data["timeout"]
        )
        
        # Calculate total cost recursively
        def calculate_total_cost(agent):
            """Recursively calculate total cost including all subagents"""
            total = agent.cost_usd
            for subagent in agent.subagents:
                total += calculate_total_cost(subagent)
            return total

        # Update task with results
        task_data["status"] = "completed"
        task_data["result"] = result
        task_data["completed_at"] = datetime.utcnow()
        task_data["agent_tree"] = root_agent.to_dict()  # Store complete agent tree
        task_data["metrics"] = {
            "prompt_tokens": root_agent.prompt_tokens,
            "completion_tokens": root_agent.completion_tokens,
            "total_tokens": root_agent.prompt_tokens + root_agent.completion_tokens,
            "total_agents": 1 + len(root_agent.subagents),
            "max_depth": root_agent.depth,
            "cost_usd": calculate_total_cost(root_agent),
            "execution_time_seconds": (
                task_data["completed_at"] - task_data["created_at"]
            ).total_seconds()
        }

        logger.info(
            "task_completed",
            task_id=str(task_id),
            total_agents=task_data["metrics"]["total_agents"]
        )
        
    except asyncio.TimeoutError:
        task_data["status"] = "timeout"
        task_data["completed_at"] = datetime.utcnow()
        task_data["agent_tree"] = root_agent.to_dict() if 'root_agent' in locals() else None
        task_data["error"] = {
            "type": "TimeoutError",
            "message": f"Task exceeded timeout of {task_data['timeout']} seconds",
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.error("task_timeout", task_id=str(task_id))

    except Exception as e:
        import traceback
        task_data["status"] = "failed"
        task_data["completed_at"] = datetime.utcnow()
        task_data["agent_tree"] = root_agent.to_dict() if 'root_agent' in locals() else None
        task_data["error"] = {
            "type": type(e).__name__,
            "message": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.error("task_failed", task_id=str(task_id), error=str(e), traceback=traceback.format_exc())

# ==========================================
# Startup
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Initialize the system"""
    logger.info(
        "mind_starting",
        model=os.getenv("MODEL_NAME", "claude-sonnet-4-5-20250929"),
        architecture="recursive_subagent"
    )
    logger.info("mind_started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("mind_shutting_down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_recursive:app", host="0.0.0.0", port=8000, reload=True)
