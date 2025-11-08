"""
Embedding generation for memory storage using Anthropic's embedding models.
"""
from typing import List
import anthropic
from anthropic import Anthropic


class EmbeddingGenerator:
    """Generates embeddings for text using Anthropic's API."""

    def __init__(self, api_key: str):
        """Initialize the embedding generator.

        Args:
            api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=api_key)

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        # Note: As of now, Anthropic doesn't have a dedicated embedding API
        # We'll use a simple hash-based approach for demo, but in production
        # you'd want to use a proper embedding model like OpenAI's or Voyage AI
        # For now, we'll create a placeholder that can be replaced
        return self._placeholder_embedding(text)

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        return [self.generate_embedding(text) for text in texts]

    def _placeholder_embedding(self, text: str) -> List[float]:
        """Placeholder embedding using text hashing.

        In production, replace this with a real embedding model like:
        - Voyage AI
        - OpenAI embeddings
        - Sentence Transformers

        Args:
            text: Text to embed

        Returns:
            1536-dimensional embedding vector
        """
        import hashlib
        import struct

        # Use hash to generate deterministic but distributed values
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()

        # Generate 1536 dimensions (standard embedding size)
        embedding = []
        for i in range(384):  # 384 * 4 = 1536 dimensions
            idx = (i * 4) % len(hash_bytes)
            # Convert 4 bytes to float
            val = struct.unpack('f', hash_bytes[idx:idx+4] + b'\x00\x00\x00\x00')[0]
            # Normalize to reasonable range
            embedding.extend([val, -val, val * 0.5, -val * 0.5])

        # Normalize the vector
        magnitude = sum(x*x for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding[:1536]  # Ensure exactly 1536 dimensions
