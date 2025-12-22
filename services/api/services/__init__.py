"""
Services for the Medical Translation API.

Business logic and external service integrations.
"""

# AI Provider Factory (recommended)
from .ai import (
    AIProviderFactory,
    get_embedding_service,
    get_transcription_service,
    get_translation_service,
)

# Legacy services (for backward compatibility)
from .gemini_service import GeminiService, get_gemini_service
from .rag_service import RAGService

__all__ = [
    # AI Factory (new)
    "AIProviderFactory",
    "get_translation_service",
    "get_embedding_service",
    "get_transcription_service",
    # Legacy
    "GeminiService",
    "get_gemini_service",
    "RAGService",
]
