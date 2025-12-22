"""
AI Service Provider Factory.

Supports multiple AI providers:
- Gemini (Google Cloud)
- Ollama (Local/Self-hosted)

Usage:
    from api.services.ai import get_translation_service, get_embedding_service

    translator = get_translation_service()
    result = translator.translate("Hello", "en", "es")
"""

from .base import (
    BaseCompletionService,
    BaseEmbeddingService,
    BaseTranscriptionService,
    BaseTranslationService,
)
from .factory import (
    AIProvider,
    AIProviderFactory,
    get_completion_service,
    get_embedding_service,
    get_transcription_service,
    get_translation_service,
)

__all__ = [
    "AIProvider",
    "AIProviderFactory",
    "get_translation_service",
    "get_embedding_service",
    "get_transcription_service",
    "get_completion_service",
    "BaseTranslationService",
    "BaseEmbeddingService",
    "BaseTranscriptionService",
    "BaseCompletionService",
]
