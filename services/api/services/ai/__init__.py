"""
AI Service Provider Factory.

Supports multiple AI providers:
- Gemini (Google Cloud)
- Ollama (Local/Self-hosted)

Usage:
    from api.services.ai import get_translation_service, get_embedding_service

    translator = get_translation_service()
    result = translator.translate("Hello", "en", "es")

Prompt Management:
    from api.services.ai.prompts import PromptVersion, get_translation_prompt

    prompt = get_translation_prompt(PromptVersion.V1)
    rendered = prompt.render(text="Hello", source_lang="English", target_lang="Spanish")
"""

from .base import (
    BaseAIService,
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
from .prompts import PromptVersion

__all__ = [
    # Factory
    "AIProvider",
    "AIProviderFactory",
    "get_translation_service",
    "get_embedding_service",
    "get_transcription_service",
    "get_completion_service",
    # Base classes
    "BaseAIService",
    "BaseTranslationService",
    "BaseEmbeddingService",
    "BaseTranscriptionService",
    "BaseCompletionService",
    # Prompts
    "PromptVersion",
]
