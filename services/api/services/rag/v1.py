"""
RAG Service V1 - Original Implementation

Character-based chunking with simple cosine similarity search.
No minimum similarity threshold.
"""

import logging
from typing import Any

from api.models import Collection, CollectionItem

from .base import BaseRAGService, RAGVersion

logger = logging.getLogger(__name__)


class RAGServiceV1(BaseRAGService):
    """
    Original RAG implementation.

    Features:
    - Character-based chunking (fixed length)
    - Window overlap option
    - Returns top_k results regardless of relevance
    - Queries linked knowledge bases for patient contexts
    """

    version = RAGVersion.V1

    def chunk_text(self, text: str) -> list[dict]:
        """
        Split text by character count.

        Uses collection's chunking_strategy setting:
        - NO_CHUNKING: Return as single chunk
        - FIXED_LENGTH: Split at chunk_length characters
        - WINDOW: Split with chunk_overlap
        """
        if self.collection.chunking_strategy == Collection.ChunkingStrategy.NO_CHUNKING:
            return [{"content": text}]

        chunk_length = self.collection.chunk_length or 1000
        chunk_overlap = self.collection.chunk_overlap or 0

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_length
            chunk_content = text[start:end]
            chunks.append(
                {
                    "content": chunk_content,
                    "start_char": start,
                    "end_char": min(end, text_length),
                }
            )

            if self.collection.chunking_strategy == Collection.ChunkingStrategy.WINDOW:
                start = end - chunk_overlap
            else:
                start = end

        return chunks

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        query_embedding: list[float] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Query with cosine similarity, no filtering.

        Returns top_k results even if similarity is low.
        """
        if query_embedding is None:
            query_embedding = self._generate_embedding(query_text)

        # Query current collection
        items = CollectionItem.objects.filter(collection=self.collection, embedding__isnull=False)

        results = []
        for item in items:
            if item.embedding:
                similarity = self._cosine_similarity(query_embedding, item.embedding)
                results.append(
                    {
                        "item": item,
                        "similarity": similarity,
                        "content": item.content,
                        "name": item.name,
                        "metadata": item.metadata,
                        "source_collection": self.collection.name,
                    }
                )

        # Query linked knowledge bases (for Patient Contexts)
        if self.collection.collection_type == Collection.CollectionType.PATIENT_CONTEXT:
            for kb in self.collection.knowledge_bases.all():
                try:
                    kb_service = RAGServiceV1(kb)
                    kb_results = kb_service.query(query_text, top_k=top_k, query_embedding=query_embedding)
                    for res in kb_results:
                        res["source_collection"] = kb.name
                        results.append(res)
                except Exception as e:
                    logger.warning(f"Failed to query linked KB {kb.name}: {e}")

        # Sort and return top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
