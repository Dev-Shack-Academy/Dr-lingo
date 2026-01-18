"""
Services for the Medical Translation API.

Business logic and external service integrations.
"""

# AI Provider Factory (recommended)
from .ai import (
    AIProviderFactory,
    get_completion_service,
    get_embedding_service,
    get_transcription_service,
    get_translation_service,
)

# Legacy services (for backward compatibility)
from .gemini_service import GeminiService, get_gemini_service

# RAG Services (versioned)
from .rag import (
    RAGVersion,
    get_rag_service,
    get_translation_context,
)

# Backward compatibility - RAGService points to factory
from .rag.v1 import RAGServiceV1 as RAGService  # Legacy alias

__all__ = [
    # AI Factory
    "AIProviderFactory",
    "get_translation_service",
    "get_embedding_service",
    "get_transcription_service",
    "get_completion_service",
    "get_image_analysis_service",
    # RAG (versioned)
    "RAGVersion",
    "get_rag_service",
    "get_translation_context",
    # Legacy (deprecated - use AI Factory instead)
    "GeminiService",
    "get_gemini_service",
    "RAGService",  # Backward compatible
]
