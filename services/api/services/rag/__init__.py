"""
RAG (Retrieval-Augmented Generation) Service Module

Provides versioned RAG implementations with:
- Configurable chunking strategies
- Similarity search with filtering
- Easy version switching via RAGVersion enum

Usage:
    from api.services.rag import get_rag_service, RAGVersion

    # Get latest (V2)
    service = get_rag_service(collection)

    # Get specific version
    service = get_rag_service(collection, version=RAGVersion.V1)
"""

from .base import BaseRAGService, RAGVersion
from .factory import get_rag_service, get_translation_context
from .v1 import RAGServiceV1
from .v2 import RAGServiceV2

__all__ = [
    "BaseRAGService",
    "RAGVersion",
    "RAGServiceV1",
    "RAGServiceV2",
    "get_rag_service",
    "get_translation_context",
]
