import logging
from enum import Enum

from django.conf import settings

from .base import (
    BaseCompletionService,
    BaseEmbeddingService,
    BaseTranscriptionService,
    BaseTranslationService,
)

logger = logging.getLogger(__name__)


class AIProvider(str, Enum):
    """Supported AI providers."""

    GEMINI = "gemini"
    OLLAMA = "ollama"


class AIProviderFactory:
    """
    Factory for creating AI service instances.

    Usage:
        factory = AIProviderFactory()
        translator = factory.get_translation_service()
        embedder = factory.get_embedding_service()
    """

    _instances: dict[str, object] = {}

    def __init__(self, provider: AIProvider | str | None = None):
        """
        Initialize factory with specified provider.

        Args:
            provider: AI provider to use. Defaults to settings.AI_PROVIDER
        """
        if provider is None:
            provider = getattr(settings, "AI_PROVIDER", "gemini")

        if isinstance(provider, str):
            provider = AIProvider(provider.lower())

        self.provider = provider

    def get_translation_service(self) -> BaseTranslationService:
        """Get translation service for configured provider."""
        cache_key = f"translation_{self.provider.value}"

        if cache_key not in self._instances:
            if self.provider == AIProvider.GEMINI:
                from .gemini_provider import GeminiTranslationService

                self._instances[cache_key] = GeminiTranslationService()
            elif self.provider == AIProvider.OLLAMA:
                from .ollama_provider import OllamaTranslationService

                self._instances[cache_key] = OllamaTranslationService()
            else:
                raise ValueError(f"Unknown provider: {self.provider}")

        return self._instances[cache_key]

    def get_embedding_service(self) -> BaseEmbeddingService:
        """Get embedding service for configured provider."""
        cache_key = f"embedding_{self.provider.value}"

        if cache_key not in self._instances:
            if self.provider == AIProvider.GEMINI:
                from .gemini_provider import GeminiEmbeddingService

                self._instances[cache_key] = GeminiEmbeddingService()
            elif self.provider == AIProvider.OLLAMA:
                from .ollama_provider import OllamaEmbeddingService

                self._instances[cache_key] = OllamaEmbeddingService()
            else:
                raise ValueError(f"Unknown provider: {self.provider}")

        return self._instances[cache_key]

    def get_transcription_service(self) -> BaseTranscriptionService:
        """
        Get transcription service.

        Note: For Ollama, falls back to Gemini if Whisper unavailable.
        """
        cache_key = f"transcription_{self.provider.value}"

        if cache_key not in self._instances:
            if self.provider == AIProvider.GEMINI:
                from .gemini_provider import GeminiTranscriptionService

                self._instances[cache_key] = GeminiTranscriptionService()
            elif self.provider == AIProvider.OLLAMA:
                # Try Ollama/Whisper first, fallback to Gemini
                from .ollama_provider import OllamaTranscriptionService

                ollama_service = OllamaTranscriptionService()

                # Check if Whisper is available
                try:
                    import requests

                    whisper_url = getattr(settings, "WHISPER_API_URL", "http://localhost:9000")
                    response = requests.get(f"{whisper_url}/health", timeout=2)
                    if response.status_code == 200:
                        self._instances[cache_key] = ollama_service
                    else:
                        raise Exception("Whisper not healthy")
                except Exception:
                    logger.warning("Whisper unavailable, using Gemini for transcription")
                    from .gemini_provider import GeminiTranscriptionService

                    self._instances[cache_key] = GeminiTranscriptionService()
            else:
                raise ValueError(f"Unknown provider: {self.provider}")

        return self._instances[cache_key]

    def get_completion_service(self) -> BaseCompletionService:
        """Get text completion service for configured provider."""
        cache_key = f"completion_{self.provider.value}"

        if cache_key not in self._instances:
            if self.provider == AIProvider.GEMINI:
                from .gemini_provider import GeminiCompletionService

                self._instances[cache_key] = GeminiCompletionService()
            elif self.provider == AIProvider.OLLAMA:
                from .ollama_provider import OllamaCompletionService

                self._instances[cache_key] = OllamaCompletionService()
            else:
                raise ValueError(f"Unknown provider: {self.provider}")

        return self._instances[cache_key]

    @classmethod
    def clear_cache(cls):
        """Clear cached service instances."""
        cls._instances.clear()


# Convenience functions for getting services with default provider
_default_factory: AIProviderFactory | None = None


def _get_factory() -> AIProviderFactory:
    """Get or create default factory."""
    global _default_factory
    if _default_factory is None:
        _default_factory = AIProviderFactory()
    return _default_factory


def get_translation_service() -> BaseTranslationService:
    """Get translation service with default provider."""
    return _get_factory().get_translation_service()


def get_embedding_service() -> BaseEmbeddingService:
    """Get embedding service with default provider."""
    return _get_factory().get_embedding_service()


def get_transcription_service() -> BaseTranscriptionService:
    """Get transcription service with default provider."""
    return _get_factory().get_transcription_service()


def get_completion_service() -> BaseCompletionService:
    """Get completion service with default provider."""
    return _get_factory().get_completion_service()
