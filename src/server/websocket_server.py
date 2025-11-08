"""
WebSocket server for real-time agent progress updates.

Provides live updates of:
- Agent execution tree
- Current agent status
- Thoughts and reasoning
- Tool calls
- Memory operations
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, Any, Optional
import json
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        """Initialize connection manager."""
        # Map of execution_id -> set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, execution_id: str):
        """Accept a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            execution_id: Execution ID to subscribe to
        """
        await websocket.accept()
        async with self._lock:
            if execution_id not in self.active_connections:
                self.active_connections[execution_id] = set()
            self.active_connections[execution_id].add(websocket)

        logger.info(f"Client connected to execution {execution_id}")

    async def disconnect(self, websocket: WebSocket, execution_id: str):
        """Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection
            execution_id: Execution ID
        """
        async with self._lock:
            if execution_id in self.active_connections:
                self.active_connections[execution_id].discard(websocket)
                if not self.active_connections[execution_id]:
                    del self.active_connections[execution_id]

        logger.info(f"Client disconnected from execution {execution_id}")

    async def broadcast(self, execution_id: str, message: Dict[str, Any]):
        """Broadcast message to all connections for an execution.

        Args:
            execution_id: Execution ID
            message: Message to broadcast
        """
        async with self._lock:
            connections = self.active_connections.get(execution_id, set()).copy()

        if not connections:
            return

        # Add timestamp
        message["timestamp"] = datetime.now().isoformat()

        # Convert to JSON
        message_json = json.dumps(message)

        # Send to all connections
        dead_connections = set()
        for connection in connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                dead_connections.add(connection)

        # Clean up dead connections
        if dead_connections:
            async with self._lock:
                if execution_id in self.active_connections:
                    self.active_connections[execution_id] -= dead_connections

    async def send_agent_created(
        self,
        execution_id: str,
        agent_id: str,
        task: str,
        depth: int,
        parent_id: Optional[str] = None
    ):
        """Send agent creation event.

        Args:
            execution_id: Execution ID
            agent_id: Agent ID
            task: Agent task
            depth: Tree depth
            parent_id: Parent agent ID
        """
        await self.broadcast(execution_id, {
            "type": "agent_created",
            "agent_id": agent_id,
            "task": task,
            "depth": depth,
            "parent_id": parent_id,
        })

    async def send_agent_status(
        self,
        execution_id: str,
        agent_id: str,
        status: str
    ):
        """Send agent status update.

        Args:
            execution_id: Execution ID
            agent_id: Agent ID
            status: New status
        """
        await self.broadcast(execution_id, {
            "type": "agent_status",
            "agent_id": agent_id,
            "status": status,
        })

    async def send_thought(
        self,
        execution_id: str,
        agent_id: str,
        thought: str,
        thought_type: str
    ):
        """Send agent thought.

        Args:
            execution_id: Execution ID
            agent_id: Agent ID
            thought: Thought text
            thought_type: Type of thought
        """
        await self.broadcast(execution_id, {
            "type": "thought",
            "agent_id": agent_id,
            "thought": thought,
            "thought_type": thought_type,
        })

    async def send_tool_call(
        self,
        execution_id: str,
        agent_id: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ):
        """Send tool call event.

        Args:
            execution_id: Execution ID
            agent_id: Agent ID
            tool_name: Name of tool
            arguments: Tool arguments
        """
        await self.broadcast(execution_id, {
            "type": "tool_call",
            "agent_id": agent_id,
            "tool_name": tool_name,
            "arguments": arguments,
        })

    async def send_evaluation(
        self,
        execution_id: str,
        agent_id: str,
        result: str,
        reasoning: str
    ):
        """Send evaluation result.

        Args:
            execution_id: Execution ID
            agent_id: Agent ID
            result: Evaluation result (accept/reject/refine)
            reasoning: Evaluation reasoning
        """
        await self.broadcast(execution_id, {
            "type": "evaluation",
            "agent_id": agent_id,
            "result": result,
            "reasoning": reasoning,
        })

    async def send_synthesis(
        self,
        execution_id: str,
        agent_id: str,
        num_subagents: int
    ):
        """Send synthesis event.

        Args:
            execution_id: Execution ID
            agent_id: Agent ID
            num_subagents: Number of sub-agents being synthesized
        """
        await self.broadcast(execution_id, {
            "type": "synthesis",
            "agent_id": agent_id,
            "num_subagents": num_subagents,
        })

    async def send_completion(
        self,
        execution_id: str,
        agent_id: str,
        output: str
    ):
        """Send completion event.

        Args:
            execution_id: Execution ID
            agent_id: Agent ID
            output: Final output
        """
        await self.broadcast(execution_id, {
            "type": "completion",
            "agent_id": agent_id,
            "output": output,
        })

    async def send_error(
        self,
        execution_id: str,
        agent_id: str,
        error: str
    ):
        """Send error event.

        Args:
            execution_id: Execution ID
            agent_id: Agent ID
            error: Error message
        """
        await self.broadcast(execution_id, {
            "type": "error",
            "agent_id": agent_id,
            "error": error,
        })


# Global connection manager
connection_manager = ConnectionManager()
