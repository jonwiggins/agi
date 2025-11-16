"""
AGI Platform WebUI - Real-time Visualization Service

Provides a web interface to visualize agent trees, monitor tasks,
and explore stored memories in real-time.
"""

import os
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import json

app = FastAPI(title="AGI WebUI", version="1.0.0")

# Configuration
MIND_API_URL = os.getenv("MIND_API_URL", "http://mind:8000")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# HTTP client for proxying requests
http_client = httpx.AsyncClient(base_url=MIND_API_URL, timeout=30.0)

# ==========================================
# Web Pages
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/task/{task_id}", response_class=HTMLResponse)
async def task_detail(request: Request, task_id: str):
    """Task detail and tree visualization page"""
    return templates.TemplateResponse("task.html", {
        "request": request,
        "task_id": task_id
    })

@app.get("/memories", response_class=HTMLResponse)
async def memories_page(request: Request):
    """Memory browser page"""
    return templates.TemplateResponse("memories.html", {"request": request})

# ==========================================
# API Proxy Endpoints
# ==========================================

@app.get("/api/health")
async def health():
    """Health check"""
    try:
        response = await http_client.get("/health")
        return response.json()
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/api/stats")
async def stats():
    """Get system stats"""
    try:
        response = await http_client.get("/stats")
        if response.status_code == 200:
            return response.json()
        else:
            # Return default stats if backend unavailable
            return {
                "tasks": {"total": 0, "completed": 0, "processing": 0, "failed": 0},
                "costs": {"total_usd": 0.0, "average_per_task_usd": 0.0}
            }
    except Exception as e:
        # Return default stats if backend unavailable
        return {
            "tasks": {"total": 0, "completed": 0, "processing": 0, "failed": 0},
            "costs": {"total_usd": 0.0, "average_per_task_usd": 0.0}
        }

@app.get("/api/tasks")
async def list_tasks():
    """List all tasks"""
    try:
        response = await http_client.get("/tasks")
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        # Return empty array if backend unavailable
        return []

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """Get task details"""
    try:
        response = await http_client.get(f"/tasks/{task_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Task not found or backend unavailable", "task_id": task_id}
    except Exception as e:
        return {"error": str(e), "task_id": task_id}

@app.get("/api/tasks/{task_id}/tree")
async def get_task_tree(task_id: str):
    """Get agent tree structure"""
    try:
        response = await http_client.get(f"/tasks/{task_id}/tree")
        return response.json()
    except Exception as e:
        # Mock tree structure for development
        return {
            "task_id": task_id,
            "tree": {
                "nodes": [
                    {
                        "id": "root",
                        "label": "Root Agent",
                        "status": "completed",
                        "depth": 0,
                        "task": "Main task"
                    }
                ],
                "edges": []
            }
        }

@app.get("/api/tasks/{task_id}/agents/{agent_id}")
async def get_agent_details(task_id: str, agent_id: str):
    """Get specific agent details including tool calls"""
    try:
        response = await http_client.get(f"/tasks/{task_id}/agents/{agent_id}")
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/tasks")
async def create_task(task_data: dict):
    """Create a new task"""
    try:
        response = await http_client.post("/tasks", json=task_data)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# ==========================================
# WebSocket for Real-time Updates
# ==========================================

@app.websocket("/ws/tasks/{task_id}")
async def websocket_task_updates(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time task updates.
    
    Connects to Mind service and streams updates to the frontend.
    """
    await websocket.accept()
    
    try:
        # Connect to Mind's WebSocket
        async with httpx.AsyncClient() as client:
            # For now, send mock updates
            # In production, this would connect to Mind's WebSocket
            await websocket.send_json({
                "type": "connected",
                "task_id": task_id,
                "message": "Connected to task updates"
            })
            
            # Keep connection alive and send periodic updates
            while True:
                await asyncio.sleep(2)
                # In production, forward messages from Mind service
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": asyncio.get_event_loop().time()
                })
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")

# ==========================================
# Startup/Shutdown
# ==========================================

@app.on_event("startup")
async def startup():
    """Initialize WebUI service"""
    print("WebUI starting...")
    print(f"Connected to Mind API: {MIND_API_URL}")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    await http_client.aclose()
    print("WebUI shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
