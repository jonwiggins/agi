"""
FastAPI server for the AGI platform.
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
from ..agent.core import AGIAgent
from ..agent.tools import ToolRegistry


# Pydantic models for API requests/responses
class ChatMessage(BaseModel):
    """A chat message."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    message: str = Field(..., description="User message")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=None,
        description="Optional conversation history"
    )
    store_in_memory: bool = Field(
        default=True,
        description="Whether to store the interaction in memory"
    )


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    response: str = Field(..., description="Agent's response")
    tool_calls: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Tools that were called"
    )
    memories_used: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Memories that were retrieved"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class MemoryRequest(BaseModel):
    """Request for adding a memory."""
    content: str = Field(..., description="Memory content")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata"
    )


class MemoryResponse(BaseModel):
    """Response from memory operations."""
    memory_id: str = Field(..., description="ID of the memory")


class MemorySearchRequest(BaseModel):
    """Request for searching memories."""
    query: str = Field(..., description="Search query")
    n_results: int = Field(default=5, description="Number of results")


class MemorySearchResponse(BaseModel):
    """Response from memory search."""
    memories: List[Dict[str, Any]] = Field(..., description="Relevant memories")


# Global agent instance
agent: Optional[AGIAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    global agent
    agent = initialize_agent()
    yield
    # Shutdown
    # Add any cleanup here if needed


# Create FastAPI app
app = FastAPI(
    title="AGI Platform API",
    description="API for interacting with the AGI agent",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def initialize_agent() -> AGIAgent:
    """Initialize the AGI agent with all components.

    Returns:
        Configured AGI agent instance
    """
    # Load configuration from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    chroma_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma")
    collection_name = os.getenv("MEMORY_COLLECTION_NAME", "agi_memories")
    default_model = os.getenv("DEFAULT_MODEL", "claude-sonnet-4-5-20250929")
    max_memory_results = int(os.getenv("MAX_MEMORY_RESULTS", "5"))
    memory_threshold = float(os.getenv("MEMORY_RELEVANCE_THRESHOLD", "0.7"))

    # Initialize components
    embedding_generator = EmbeddingGenerator(api_key=api_key)
    memory_store = MemoryStore(
        persist_directory=chroma_dir,
        collection_name=collection_name,
        embedding_generator=embedding_generator,
    )
    api_client = AnthropicClient(api_key=api_key, default_model=default_model)
    tool_registry = ToolRegistry()

    # Register built-in tools
    register_builtin_tools(tool_registry, memory_store)

    # Create agent
    return AGIAgent(
        api_client=api_client,
        memory_store=memory_store,
        tool_registry=tool_registry,
        max_memory_results=max_memory_results,
        memory_relevance_threshold=memory_threshold,
    )


def register_builtin_tools(registry: ToolRegistry, memory_store: MemoryStore):
    """Register built-in tools.

    Args:
        registry: Tool registry
        memory_store: Memory store instance
    """
    from ..agent.tools import Tool, ToolParameter, ToolParameterType

    # Add memory tool
    def add_memory_tool(content: str, metadata_json: str = "{}") -> dict:
        """Add a new memory to the system."""
        import json
        metadata = json.loads(metadata_json) if metadata_json else {}
        memory_id = memory_store.add_memory(content=content, metadata=metadata)
        return {"memory_id": memory_id, "status": "success"}

    registry.register_tool_direct(Tool(
        name="add_memory",
        description="Store important information in long-term memory for future reference",
        parameters=[
            ToolParameter(
                name="content",
                type=ToolParameterType.STRING,
                description="The information to remember",
                required=True,
            ),
            ToolParameter(
                name="metadata_json",
                type=ToolParameterType.STRING,
                description="Optional JSON metadata to attach to the memory",
                required=False,
            ),
        ],
        function=add_memory_tool,
    ))


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AGI Platform API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with the AGI agent.

    Args:
        request: Chat request with message and optional history

    Returns:
        Agent's response with metadata
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        # Convert conversation history to dict format
        conversation_history = None
        if request.conversation_history:
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

        # Process message
        response = agent.process_message(
            user_message=request.message,
            conversation_history=conversation_history,
            store_in_memory=request.store_in_memory,
        )

        return ChatResponse(
            response=response.content,
            tool_calls=response.tool_calls,
            memories_used=response.memories_used,
            metadata=response.metadata,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory", response_model=MemoryResponse)
async def add_memory(request: MemoryRequest):
    """Add a memory to the system.

    Args:
        request: Memory content and metadata

    Returns:
        Memory ID
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        memory_id = agent.add_memory(
            content=request.content,
            metadata=request.metadata,
        )
        return MemoryResponse(memory_id=memory_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/search", response_model=MemorySearchResponse)
async def search_memories(request: MemorySearchRequest):
    """Search for memories.

    Args:
        request: Search query and parameters

    Returns:
        Relevant memories
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        memories = agent.search_memories(
            query=request.query,
            n_results=request.n_results,
        )
        return MemorySearchResponse(memories=memories)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools")
async def list_tools():
    """List available tools.

    Returns:
        List of tool names and definitions
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


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(app, host=host, port=port)
