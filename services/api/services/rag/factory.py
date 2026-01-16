"""
RAG Service Factory

Provides factory functions for getting RAG services and translation context.
"""

import logging
from typing import Any

from django.conf import settings

from api.models import Collection

from .base import BaseRAGService, RAGVersion
from .v1 import RAGServiceV1
from .v2 import RAGServiceV2

logger = logging.getLogger(__name__)

# Registry of RAG service versions
_RAG_SERVICES: dict[RAGVersion, type[BaseRAGService]] = {
    RAGVersion.V1: RAGServiceV1,
    RAGVersion.V2: RAGServiceV2,
    RAGVersion.LATEST: RAGServiceV2,  # V2 is now the default
}

# Default version (can be overridden in settings)
DEFAULT_RAG_VERSION = RAGVersion.LATEST


def get_rag_service(collection: Collection, version: RAGVersion | None = None, **kwargs) -> BaseRAGService:
    """
    Get a RAG service for a collection.

    Args:
        collection: The Collection to query
        version: RAG version (V1, V2, or LATEST). Defaults to settings or LATEST.
        **kwargs: Additional arguments passed to service constructor

    Returns:
        RAG service instance

    Example:
        from api.services.rag import get_rag_service, RAGVersion

        # Get latest version
        service = get_rag_service(collection)

        # Get specific version
        service = get_rag_service(collection, version=RAGVersion.V1)
    """
    if version is None:
        # Check settings for default version
        version_str = getattr(settings, "RAG_VERSION", None)
        if version_str:
            try:
                version = RAGVersion(version_str)
            except ValueError:
                logger.warning(f"Invalid RAG_VERSION in settings: {version_str}")
                version = DEFAULT_RAG_VERSION
        else:
            version = DEFAULT_RAG_VERSION

    service_class = _RAG_SERVICES.get(version)
    if not service_class:
        raise ValueError(f"Unknown RAG version: {version}")

    return service_class(collection, **kwargs)


def query_global_knowledge_base(
    query_text: str,
    top_k: int = 5,
    version: RAGVersion | None = None,
) -> list[dict[str, Any]]:
    """
    Query all global knowledge base collections.

    Generates embedding once and reuses across all collections.
    """
    global_collections = Collection.objects.filter(
        collection_type=Collection.CollectionType.KNOWLEDGE_BASE, is_global=True
    )

    if not global_collections.exists():
        logger.info("No global knowledge base collections found.")
        return []

    all_results = []
    query_embedding = None

    # Generate embedding once
    try:
        first_service = get_rag_service(global_collections[0], version=version)
        query_embedding = first_service._generate_embedding(query_text)
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return []

    for collection in global_collections:
        try:
            service = get_rag_service(collection, version=version)
            results = service.query(
                query_text,
                top_k=top_k * 2,  # Get more, filter later
                query_embedding=query_embedding,
            )
            for result in results:
                result["collection_name"] = collection.name
            all_results.extend(results)
        except Exception as e:
            logger.warning(f"Error querying {collection.name}: {e}")

    all_results.sort(key=lambda x: x["similarity"], reverse=True)
    return all_results[:top_k]


def query_patient_context(
    chat_room_id: int,
    query_text: str,
    top_k: int = 3,
    version: RAGVersion | None = None,
) -> list[dict[str, Any]]:
    """
    Query patient context collections for a chat room.
    """
    patient_collections = Collection.objects.filter(
        collection_type=Collection.CollectionType.PATIENT_CONTEXT, chat_room_id=chat_room_id
    ).prefetch_related("knowledge_bases")

    if not patient_collections.exists():
        return []

    all_results = []
    query_embedding = None

    # Generate embedding once
    try:
        first_service = get_rag_service(patient_collections[0], version=version)
        query_embedding = first_service._generate_embedding(query_text)
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return []

    for collection in patient_collections:
        try:
            service = get_rag_service(collection, version=version)
            results = service.query(query_text, top_k=top_k, query_embedding=query_embedding)
            for result in results:
                result["collection_name"] = collection.name
                result["is_patient_context"] = True
            all_results.extend(results)
        except Exception as e:
            logger.warning(f"Error querying patient context: {e}")

    all_results.sort(key=lambda x: x["similarity"], reverse=True)
    return all_results[:top_k]


def get_translation_context(
    chat_room_id: int,
    text: str,
    top_k: int = 5,
    version: RAGVersion | None = None,
) -> dict[str, Any]:
    """
    Get combined context for translation.

    This is the main function called by translation tasks.
    Combines:
    1. Global knowledge base (medical terms, grammar rules)
    2. Patient-specific context (history, preferences)

    Args:
        chat_room_id: Chat room ID for patient context
        text: Text being translated (used as query)
        top_k: Max results from knowledge base
        version: RAG version to use

    Returns:
        Dict with knowledge_base, patient_context, and has_context flag
    """
    # Get global knowledge base context
    kb_results = query_global_knowledge_base(text, top_k=top_k, version=version)

    # Get patient-specific context
    patient_results = query_patient_context(chat_room_id, text, top_k=3, version=version)

    return {
        "knowledge_base": [
            {
                "name": r["name"],
                "content": r["content"],
                "collection": r.get("collection_name", ""),
                "relevance": round(r["similarity"], 3),
            }
            for r in kb_results
        ],
        "patient_context": [
            {
                "name": r["name"],
                "content": r["content"],
                "collection": r.get("collection_name", ""),
                "relevance": round(r["similarity"], 3),
            }
            for r in patient_results
        ],
        "has_context": len(kb_results) > 0 or len(patient_results) > 0,
    }
