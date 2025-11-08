"""
Memory storage using ChromaDB for vector-based retrieval.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings
from .embeddings import EmbeddingGenerator


class MemoryStore:
    """Manages long-term memory storage and retrieval using ChromaDB."""

    def __init__(
        self,
        persist_directory: str,
        collection_name: str,
        embedding_generator: EmbeddingGenerator,
    ):
        """Initialize the memory store.

        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the ChromaDB collection
            embedding_generator: Embedding generator instance
        """
        self.embedding_generator = embedding_generator

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "AGI long-term memory storage"}
        )

    def add_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None,
    ) -> str:
        """Add a new memory to the store.

        Args:
            content: The text content of the memory
            metadata: Optional metadata to attach to the memory
            memory_id: Optional custom ID for the memory

        Returns:
            The ID of the stored memory
        """
        # Generate embedding
        embedding = self.embedding_generator.generate_embedding(content)

        # Generate ID if not provided
        if memory_id is None:
            memory_id = f"mem_{datetime.now().timestamp()}"

        # Add timestamp to metadata
        if metadata is None:
            metadata = {}
        metadata["timestamp"] = datetime.now().isoformat()

        # Store in ChromaDB
        self.collection.add(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata],
        )

        return memory_id

    def search_memories(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for relevant memories based on a query.

        Args:
            query: The search query
            n_results: Maximum number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of relevant memories with content, metadata, and relevance scores
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)

        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata,
        )

        # Format results
        memories = []
        if results["documents"] and len(results["documents"]) > 0:
            for i in range(len(results["documents"][0])):
                memory = {
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0.0,
                    "relevance": 1 - (results["distances"][0][i] if results["distances"] else 0.0),
                }
                memories.append(memory)

        return memories

    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory by ID.

        Args:
            memory_id: The ID of the memory

        Returns:
            The memory dict or None if not found
        """
        result = self.collection.get(ids=[memory_id])

        if result["documents"] and len(result["documents"]) > 0:
            return {
                "id": result["ids"][0],
                "content": result["documents"][0],
                "metadata": result["metadatas"][0] if result["metadatas"] else {},
            }
        return None

    def delete_memory(self, memory_id: str):
        """Delete a memory by ID.

        Args:
            memory_id: The ID of the memory to delete
        """
        self.collection.delete(ids=[memory_id])

    def get_all_memories(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve all memories.

        Args:
            limit: Optional limit on number of memories to return

        Returns:
            List of all memories
        """
        result = self.collection.get(limit=limit)

        memories = []
        if result["documents"]:
            for i in range(len(result["documents"])):
                memory = {
                    "id": result["ids"][i],
                    "content": result["documents"][i],
                    "metadata": result["metadatas"][i] if result["metadatas"] else {},
                }
                memories.append(memory)

        return memories

    def clear_all_memories(self):
        """Clear all memories from the store. Use with caution!"""
        # Delete and recreate collection
        self.client.delete_collection(name=self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            metadata={"description": "AGI long-term memory storage"}
        )
