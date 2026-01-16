"""
RAG Service V2 - Improved Implementation

Sentence-based chunking with relevance filtering.
"""

import logging
import re
from typing import Any

from api.models import Collection, CollectionItem

from .base import BaseRAGService, RAGVersion

logger = logging.getLogger(__name__)

# Default minimum similarity to consider a result relevant
DEFAULT_MIN_SIMILARITY = 0.25


class RAGServiceV2(BaseRAGService):
    """
    Improved RAG implementation.

    Features:
    - Sentence-aware chunking (respects semantic boundaries)
    - Paragraph-aware chunking for structured documents
    - Minimum similarity threshold (filters irrelevant results)
    - Hybrid scoring option (embedding + keyword)
    """

    version = RAGVersion.V2

    def __init__(self, collection: Collection, min_similarity: float = DEFAULT_MIN_SIMILARITY):
        super().__init__(collection)
        self.min_similarity = min_similarity

    # =========================================================================
    # SENTENCE SPLITTING
    # =========================================================================

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences, handling abbreviations."""
        # Protect common abbreviations
        protected = [
            (r"\b(Dr|Mr|Mrs|Ms|Prof|Sr|Jr)\.\s", r"\1<DOT> "),
            (r"\b(etc|vs|i\.e|e\.g|no|vol)\.\s", r"\1<DOT> "),
            (r"(\d)\.\s", r"\1<DOT> "),  # Numbers like "1. "
        ]

        for pattern, replacement in protected:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Split on sentence endings
        sentences = re.split(r"(?<=[.!?])\s+", text)

        # Restore dots
        sentences = [s.replace("<DOT>", ".") for s in sentences]

        return [s.strip() for s in sentences if s.strip()]

    # =========================================================================
    # CHUNKING STRATEGIES
    # =========================================================================

    def _chunk_by_sentences(self, text: str, max_chunk_size: int = 800, overlap_sentences: int = 1) -> list[dict]:
        """Chunk by sentences with overlap."""
        sentences = self._split_into_sentences(text)

        if not sentences:
            return [{"content": text, "chunk_type": "single"}]

        chunks = []
        current_chunk = []
        current_size = 0

        for i, sentence in enumerate(sentences):
            sentence_size = len(sentence)

            # If adding this sentence exceeds limit, save current chunk
            if current_size + sentence_size > max_chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(
                    {
                        "content": chunk_text,
                        "chunk_type": "sentences",
                        "sentence_count": len(current_chunk),
                    }
                )

                # Keep last N sentences for overlap
                if overlap_sentences > 0 and len(current_chunk) > overlap_sentences:
                    current_chunk = current_chunk[-overlap_sentences:]
                    current_size = sum(len(s) for s in current_chunk)
                else:
                    current_chunk = []
                    current_size = 0

            current_chunk.append(sentence)
            current_size += sentence_size + 1  # +1 for space

        # Last chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(
                {
                    "content": chunk_text,
                    "chunk_type": "sentences",
                    "sentence_count": len(current_chunk),
                }
            )

        return chunks

    def _chunk_by_paragraphs(self, text: str, max_chunk_size: int = 1200) -> list[dict]:
        """Chunk by paragraphs, keeping related content together."""
        paragraphs = re.split(r"\n\s*\n", text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        if not paragraphs:
            return [{"content": text, "chunk_type": "single"}]

        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)

            # Large paragraph - sub-chunk by sentences
            if para_size > max_chunk_size:
                if current_chunk:
                    chunks.append(
                        {
                            "content": "\n\n".join(current_chunk),
                            "chunk_type": "paragraphs",
                            "paragraph_count": len(current_chunk),
                        }
                    )
                    current_chunk = []
                    current_size = 0

                sub_chunks = self._chunk_by_sentences(para, max_chunk_size)
                chunks.extend(sub_chunks)
                continue

            if current_size + para_size > max_chunk_size and current_chunk:
                chunks.append(
                    {
                        "content": "\n\n".join(current_chunk),
                        "chunk_type": "paragraphs",
                        "paragraph_count": len(current_chunk),
                    }
                )
                current_chunk = []
                current_size = 0

            current_chunk.append(para)
            current_size += para_size

        if current_chunk:
            chunks.append(
                {
                    "content": "\n\n".join(current_chunk),
                    "chunk_type": "paragraphs",
                    "paragraph_count": len(current_chunk),
                }
            )

        return chunks

    def chunk_text(self, text: str) -> list[dict]:
        """
        Smart chunking based on content structure.

        - Short text (<500 chars): No chunking
        - Multiple paragraphs: Paragraph-based
        - Otherwise: Sentence-based
        """
        if len(text) < 500:
            return [{"content": text, "chunk_type": "full"}]

        # Detect structure
        paragraph_count = len(re.split(r"\n\s*\n", text))

        if paragraph_count >= 3:
            return self._chunk_by_paragraphs(text)
        else:
            return self._chunk_by_sentences(text)

    # =========================================================================
    # QUERYING WITH FILTERING
    # =========================================================================

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        query_embedding: list[float] | None = None,
        min_similarity: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Query with relevance filtering.

        Only returns results above min_similarity threshold.
        """
        if query_embedding is None:
            query_embedding = self._generate_embedding(query_text)

        threshold = min_similarity if min_similarity is not None else self.min_similarity

        items = CollectionItem.objects.filter(collection=self.collection, embedding__isnull=False)

        results = []
        for item in items:
            if not item.embedding:
                continue

            similarity = self._cosine_similarity(query_embedding, item.embedding)

            # FILTER: Skip if below threshold
            if similarity < threshold:
                continue

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

        # Query linked knowledge bases
        if self.collection.collection_type == Collection.CollectionType.PATIENT_CONTEXT:
            for kb in self.collection.knowledge_bases.all():
                try:
                    kb_service = RAGServiceV2(kb, min_similarity=threshold)
                    kb_results = kb_service.query(query_text, top_k=top_k, query_embedding=query_embedding)
                    for res in kb_results:
                        res["source_collection"] = kb.name
                        results.append(res)
                except Exception as e:
                    logger.warning(f"Failed to query linked KB {kb.name}: {e}")

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def query_hybrid(
        self,
        query_text: str,
        top_k: int = 5,
        initial_k: int = 20,
        embedding_weight: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        Hybrid search: embedding similarity + keyword overlap.

        Two-stage retrieval:
        1. Get initial_k by embedding similarity
        2. Rerank by combined score
        """
        # Stage 1: Embedding search with lower threshold
        initial_results = self.query(query_text, top_k=initial_k, min_similarity=0.15)

        if not initial_results:
            return []

        # Stage 2: Keyword scoring
        query_words = set(query_text.lower().split())

        for result in initial_results:
            content_words = set(result["content"].lower().split())
            overlap = len(query_words & content_words)
            keyword_score = overlap / max(len(query_words), 1)

            # Combined score
            result["keyword_score"] = keyword_score
            result["combined_score"] = embedding_weight * result["similarity"] + (1 - embedding_weight) * keyword_score

        initial_results.sort(key=lambda x: x["combined_score"], reverse=True)
        return initial_results[:top_k]
