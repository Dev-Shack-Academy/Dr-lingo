import logging
import math
from typing import Any

from api.models import Collection, CollectionItem

logger = logging.getLogger(__name__)


class RAGService:
    """Service for managing RAG collections and querying documents."""

    def __init__(self, collection: Collection):
        self.collection = collection
        self._setup_client()

    def _setup_client(self):
        """Initialize the embedding client based on provider."""
        # Use AI factory to get services based on collection's provider or global setting
        provider = self.collection.embedding_provider

        if provider == Collection.EmbeddingProvider.GEMINI:
            from api.services.ai import AIProvider, AIProviderFactory

            self._factory = AIProviderFactory(AIProvider.GEMINI)
        elif provider == Collection.EmbeddingProvider.OLLAMA:
            from api.services.ai import AIProvider, AIProviderFactory

            self._factory = AIProviderFactory(AIProvider.OLLAMA)
        else:
            # Use default provider from settings
            from api.services.ai import AIProviderFactory

            self._factory = AIProviderFactory()

        self._embedding_service = self._factory.get_embedding_service()
        self._completion_service = self._factory.get_completion_service()

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into chunks based on collection's chunking strategy."""
        if self.collection.chunking_strategy == Collection.ChunkingStrategy.NO_CHUNKING:
            return [text]

        chunk_length = self.collection.chunk_length or 1000
        chunk_overlap = self.collection.chunk_overlap or 0

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_length
            chunk = text[start:end]
            chunks.append(chunk)

            if self.collection.chunking_strategy == Collection.ChunkingStrategy.WINDOW:
                start = end - chunk_overlap
            else:
                start = end

        return chunks

    def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text using configured provider."""
        try:
            return self._embedding_service.generate_embedding(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def add_document(
        self, name: str, content: str, description: str = "", metadata: dict | None = None
    ) -> CollectionItem:
        """Add a document to the collection with embeddings."""
        embedding = self._generate_embedding(content)

        item = CollectionItem.objects.create(
            collection=self.collection,
            name=name,
            description=description,
            content=content,
            metadata=metadata or {},
            embedding=embedding,
        )

        logger.info(f"Added document '{name}' to collection '{self.collection.name}'")
        return item

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def query(self, query_text: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Query the collection and return most relevant documents."""
        query_embedding = self._generate_embedding(query_text)

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
                    }
                )

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def generate_answer(self, query_text: str, context_docs: list[dict[str, Any]]) -> str:
        """Generate an answer using retrieved documents as context."""
        context = "\n\n".join([f"Document: {doc['name']}\n{doc['content']}" for doc in context_docs])

        prompt = f"""Based on the following documents, answer the question.

Question: {query_text}

Answer:"""

        try:
            return self._completion_service.generate_with_context(prompt, context)
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Error generating answer: {str(e)}"

    def query_and_answer(self, query_text: str, top_k: int = 5) -> dict[str, Any]:
        """Query collection and generate an answer based on retrieved documents."""
        results = self.query(query_text, top_k=top_k)

        if not results:
            return {"status": "error", "message": "No relevant documents found", "answer": None, "sources": []}

        answer = self.generate_answer(query_text, results)

        return {
            "status": "success",
            "answer": answer,
            "sources": [
                {"name": r["name"], "similarity": r["similarity"], "content": r["content"][:200] + "..."}
                for r in results
            ],
        }


def query_global_knowledge_base(query_text: str, top_k: int = 5) -> list[dict[str, Any]]:
    """
    Query all global knowledge base collections and return combined results.

    This function queries all collections marked as knowledge_base type and is_global=True,
    combining results from all of them for comprehensive context.
    """
    global_collections = Collection.objects.filter(
        collection_type=Collection.CollectionType.KNOWLEDGE_BASE, is_global=True
    )

    all_results = []

    for collection in global_collections:
        try:
            rag_service = RAGService(collection)
            results = rag_service.query(query_text, top_k=top_k)
            for result in results:
                result["collection_name"] = collection.name
            all_results.extend(results)
        except Exception as e:
            logger.warning(f"Error querying collection {collection.name}: {e}")
            continue

    # Sort all results by similarity and return top_k
    all_results.sort(key=lambda x: x["similarity"], reverse=True)
    return all_results[:top_k]


def query_patient_context(chat_room_id: int, query_text: str, top_k: int = 3) -> list[dict[str, Any]]:
    """
    Query patient context collections linked to a specific chat room.

    Also queries any knowledge bases linked to the patient context.
    Returns relevant patient details for personalized translations.
    """
    patient_collections = Collection.objects.filter(
        collection_type=Collection.CollectionType.PATIENT_CONTEXT, chat_room_id=chat_room_id
    ).prefetch_related("knowledge_bases")

    all_results = []
    linked_kb_ids = set()

    for collection in patient_collections:
        # Query the patient context itself
        try:
            rag_service = RAGService(collection)
            results = rag_service.query(query_text, top_k=top_k)
            for result in results:
                result["collection_name"] = collection.name
                result["is_patient_context"] = True
            all_results.extend(results)
        except Exception as e:
            logger.warning(f"Error querying patient context {collection.name}: {e}")

        # Collect linked knowledge base IDs
        for kb in collection.knowledge_bases.all():
            linked_kb_ids.add(kb.id)

    # Query linked knowledge bases (patient-specific, not global)
    for kb_id in linked_kb_ids:
        try:
            kb = Collection.objects.get(id=kb_id)
            rag_service = RAGService(kb)
            results = rag_service.query(query_text, top_k=top_k)
            for result in results:
                result["collection_name"] = kb.name
                result["is_linked_kb"] = True
            all_results.extend(results)
        except Exception as e:
            logger.warning(f"Error querying linked KB {kb_id}: {e}")
            continue

    all_results.sort(key=lambda x: x["similarity"], reverse=True)
    return all_results[:top_k]


def get_translation_context(chat_room_id: int, text: str, top_k: int = 5) -> dict[str, Any]:
    """
    Get combined context from knowledge base and patient context for translation.

    This is the main function to call when translating messages - it combines:
    1. Global knowledge base (medical terms, language guides, regional info)
    2. Patient-specific context (medical history, cultural background, preferences)
    """
    # Get global knowledge base context
    kb_results = query_global_knowledge_base(text, top_k=top_k)

    # Get patient-specific context
    patient_results = query_patient_context(chat_room_id, text, top_k=3)

    return {
        "knowledge_base": [
            {
                "name": r["name"],
                "content": r["content"],
                "collection": r.get("collection_name", ""),
                "relevance": r["similarity"],
            }
            for r in kb_results
        ],
        "patient_context": [
            {
                "name": r["name"],
                "content": r["content"],
                "collection": r.get("collection_name", ""),
                "relevance": r["similarity"],
            }
            for r in patient_results
        ],
        "has_context": len(kb_results) > 0 or len(patient_results) > 0,
    }
