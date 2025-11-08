"""
FastAPI server for the Recursive AGI platform.

This server uses the recursive sub-agent architecture for complex task solving.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os
from contextlib import asynccontextmanager

from ..api.client import AnthropicClient
from ..memory.embeddings import EmbeddingGenerator
from ..memory.store import MemoryStore
from ..agent.recursive_agent import RecursiveAgent, AgentContext, AgentThought
from ..agent.enhanced_tools import create_enhanced_registry


# Pydantic models
class RecursiveTaskRequest(BaseModel):
    """Request for executing a task with recursive agents."""
    task: str = Field(..., description="The task to execute")
    max_depth: int = Field(default=5, description="Maximum recursion depth")
    max_iterations: int = Field(default=3, description="Maximum refinement iterations")
    store_in_memory: bool = Field(default=True, description="Store results in memory")


class RecursiveTaskResponse(BaseModel):
    """Response from recursive task execution."""
    agent_id: str = Field(..., description="Root agent ID")
    task: str = Field(..., description="Original task")
    output: str = Field(..., description="Final output")
    thoughts: str = Field(..., description="Agent reasoning and thoughts")
    execution_tree: Dict[str, Any] = Field(..., description="Complete execution tree")
    tool_calls: List[Dict[str, Any]] = Field(..., description="All tool calls made")
    status: str = Field(..., description="Execution status")


class AgentTreeNode(BaseModel):
    """Node in the agent execution tree."""
    agent_id: str
    task: str
    depth: int
    status: str
    children: List[str]
    thoughts: List[Dict[str, Any]]


class AgentTreeResponse(BaseModel):
    """Response containing the full agent tree."""
    tree: Dict[str, AgentTreeNode]


# Global agent instance
agent: Optional[RecursiveAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    global agent
    agent = initialize_agent()
    yield


# Create FastAPI app
app = FastAPI(
    title="Recursive AGI Platform API",
    description="API for recursive sub-agent task solving with ultrathink and validation",
    version="0.2.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def initialize_agent() -> RecursiveAgent:
    """Initialize the recursive AGI agent.

    Returns:
        Configured RecursiveAgent instance
    """
    # Load configuration
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

    # Create enhanced tool registry
    tool_registry = create_enhanced_registry(memory_store=memory_store)

    # Create recursive agent
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
        "name": "Recursive AGI Platform API",
        "version": "0.2.0",
        "architecture": "recursive_subagent",
        "capabilities": [
            "Task decomposition",
            "Sub-agent spawning",
            "Result evaluation",
            "Iterative refinement",
            "Web search",
            "Memory operations",
            "Code execution",
        ],
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/execute", response_model=RecursiveTaskResponse)
async def execute_task(request: RecursiveTaskRequest):
    """Execute a task using recursive sub-agents.

    This endpoint:
    1. Analyzes the task (ultrathink)
    2. Decides on decomposition strategy
    3. Spawns sub-agents if needed
    4. Evaluates and validates results
    5. Synthesizes final answer

    Args:
        request: Task execution request

    Returns:
        Complete execution results with tree
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Override agent settings if provided
        if request.max_depth != agent.max_depth:
            agent.max_depth = request.max_depth
        if request.max_iterations != agent.max_iterations:
            agent.max_iterations = request.max_iterations

        # Execute task
        result = agent.execute_task(request.task)

        # Store in memory if requested
        if request.store_in_memory:
            agent.memory_store.add_memory(
                content=f"Task: {request.task}\n\nResult: {result.output}",
                metadata={
                    "type": "task_execution",
                    "task": request.task,
                    "agent_id": result.agent_id,
                    "status": result.status.value,
                }
            )

        # Get execution tree
        execution_tree = agent.get_execution_tree()

        return RecursiveTaskResponse(
            agent_id=result.agent_id,
            task=request.task,
            output=result.output,
            thoughts=result.thoughts,
            execution_tree=execution_tree,
            tool_calls=result.tool_calls,
            status=result.status.value,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tree/{agent_id}", response_model=AgentTreeResponse)
async def get_agent_tree(agent_id: str):
    """Get the execution tree for a specific agent.

    Args:
        agent_id: Root agent ID

    Returns:
        Complete execution tree
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        tree = agent.get_execution_tree()

        # Format tree with thoughts
        formatted_tree = {}
        for aid, node in tree.items():
            thoughts = agent.get_agent_thoughts(aid)
            formatted_tree[aid] = AgentTreeNode(
                agent_id=aid,
                task=node["task"],
                depth=node["depth"],
                status=node["status"].value if hasattr(node["status"], "value") else str(node["status"]),
                children=node["children"],
                thoughts=[
                    {
                        "timestamp": t.timestamp,
                        "thought": t.thought,
                        "type": t.thought_type,
                    }
                    for t in thoughts
                ]
            )

        return AgentTreeResponse(tree=formatted_tree)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools")
async def list_tools():
    """List all available tools.

    Returns:
        List of tool definitions
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        tool_definitions = agent.tool_registry.get_tool_definitions()
        return {
            "tools": tool_definitions,
            "count": len(tool_definitions),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/search")
async def search_memories(query: str, n_results: int = 5):
    """Search memory database.

    Args:
        query: Search query
        n_results: Number of results

    Returns:
        Search results
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        memories = agent.memory_store.search_memories(
            query=query,
            n_results=n_results,
        )
        return {
            "query": query,
            "num_results": len(memories),
            "results": memories,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/store")
async def store_memory(content: str, metadata: Optional[Dict[str, Any]] = None):
    """Store data in memory.

    Args:
        content: Content to store
        metadata: Optional metadata

    Returns:
        Storage result
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        memory_id = agent.memory_store.add_memory(
            content=content,
            metadata=metadata or {},
        )
        return {
            "status": "success",
            "memory_id": memory_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(app, host=host, port=port)
