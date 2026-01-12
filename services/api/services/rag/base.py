"""
Base RAG Service Classes

Abstract base class and version enum for RAG implementations.
"""

import logging
import math
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from api.models import Collection, CollectionItem

logger = logging.getLogger(__name__)


class RAGVersion(str, Enum):
    """RAG service version identifiers."""

    V1 = "v1"  # Original character-based chunking
    V2 = "v2"  # Improved sentence-based chunking with filtering
    LATEST = "latest"  # Points to V2


class BaseRAGService(ABC):
    """
    Abstract base class for RAG services.

    All RAG implementations must inherit from this and implement:
    - chunk_text(): How to split documents
    - query(): How to search and rank results
    """

    version: RAGVersion = RAGVersion.V1

    def __init__(self, collection: Collection):
        self.collection = collection
        self._setup_client()

    def _setup_client(self):
        """Initialize embedding and completion services."""
        from api.services.ai import AIProviderFactory

        provider = self.collection.embedding_provider
        self._factory = AIProviderFactory(provider)

        embedding_model = getattr(self.collection, "embedding_model", None)
        completion_model = getattr(self.collection, "completion_model", None)

        self._embedding_service = self._factory.get_embedding_service(model_name=embedding_model)
        self._completion_service = self._factory.get_completion_service(model_name=completion_model)

    def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text."""
        try:
            return self._embedding_service.generate_embedding(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    @abstractmethod
    def chunk_text(self, text: str) -> list[dict]:
        """
        Split text into chunks.

        Args:
            text: Full text to chunk

        Returns:
            List of dicts with 'content' and metadata
        """
        pass

    @abstractmethod
    def query(
        self,
        query_text: str,
        top_k: int = 5,
        query_embedding: list[float] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Query the collection for relevant documents.

        Args:
            query_text: Search query
            top_k: Maximum results to return
            query_embedding: Pre-computed embedding (optional)

        Returns:
            List of results with similarity scores
        """
        pass

    def add_document(
        self, name: str, content: str, description: str = "", metadata: dict | None = None
    ) -> list[CollectionItem]:
        """
        Add a document to the collection with embeddings.

        Chunks the content and creates CollectionItem for each chunk.
        """
        chunks = self.chunk_text(content)
        items = []

        for i, chunk_data in enumerate(chunks):
            chunk_content = chunk_data.get("content", chunk_data) if isinstance(chunk_data, dict) else chunk_data
            item_name = f"{name} (Part {i+1}/{len(chunks)})" if len(chunks) > 1 else name

            embedding = self._generate_embedding(chunk_content)

            chunk_metadata = {
                **(metadata or {}),
                "chunk_index": i,
                "total_chunks": len(chunks),
                "rag_version": self.version.value,
            }

            # Add chunk-specific metadata if available
            if isinstance(chunk_data, dict):
                for k, v in chunk_data.items():
                    if k != "content":
                        chunk_metadata[k] = v

            item = CollectionItem.objects.create(
                collection=self.collection,
                name=item_name,
                description=description,
                content=chunk_content,
                metadata=chunk_metadata,
                embedding=embedding,
            )
            items.append(item)

        logger.info(
            f"[RAG {self.version.value}] Added '{name}' " f"({len(chunks)} chunks) to '{self.collection.name}'"
        )
        return items

    def generate_answer(self, query_text: str, context_docs: list[dict[str, Any]]) -> str:
        """Generate an answer using retrieved documents as context."""
        context = "\n\n".join([f"Document: {doc['name']}\n{doc['content']}" for doc in context_docs])

        try:
            return self._completion_service.generate_with_context(query_text, context)
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Error generating answer: {str(e)}"

    def query_and_answer(self, query_text: str, top_k: int = 5) -> dict[str, Any]:
        """Query collection and generate an answer."""
        results = self.query(query_text, top_k=top_k)

        if not results:
            return {"status": "error", "message": "No relevant documents found", "answer": None, "sources": []}

        answer = self.generate_answer(query_text, results)

        return {
            "status": "success",
            "answer": answer,
            "sources": [
                {"name": r["name"], "similarity": round(r["similarity"], 3), "content": r["content"][:200] + "..."}
                for r in results
            ],
        }
