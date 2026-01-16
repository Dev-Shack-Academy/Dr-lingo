import logging
from enum import Enum

from django.conf import settings

from .base import (
    BaseCompletionService,
    BaseEmbeddingService,
    BaseImageAnalysisService,
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

    def __init__(self, provider: AIProvider | str | None = None):
        """
        Initialize factory with specified provider.

        Args:
            provider: AI provider to use. Defaults to settings.AI_PROVIDER
        """
        if provider is None:
            provider = getattr(settings, "AI_PROVIDER", "ollama")

        if isinstance(provider, str):
            provider = AIProvider(provider.lower())

        self.provider = provider
        logger.info(f"AIProviderFactory initialized with provider: {self.provider.value}")
        # Instance-level cache (not class-level) so each factory has its own instances
        self._instances: dict[str, object] = {}

    def get_translation_service(self, model_name: str | None = None) -> BaseTranslationService:
        """
        Get translation service for configured provider.

        Args:
            model_name: Optional model to override defaults
        """
        # Include model in cache key if provided
        cache_suffix = f"_{model_name}" if model_name else ""
        cache_key = f"translation_{self.provider.value}{cache_suffix}"

        if cache_key not in self._instances:
            kwargs = {"model_name": model_name} if model_name else {}
            if self.provider == AIProvider.GEMINI:
                from .gemini_provider import GeminiTranslationService

                self._instances[cache_key] = GeminiTranslationService(**kwargs)
            elif self.provider == AIProvider.OLLAMA:
                from .ollama_provider import OllamaTranslationService

                self._instances[cache_key] = OllamaTranslationService(**kwargs)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")

        return self._instances[cache_key]

    def get_embedding_service(self, model_name: str | None = None) -> BaseEmbeddingService:
        """
        Get embedding service for configured provider.

        Args:
            model_name: Optional model to override defaults
        """
        # Include model in cache key if provided
        cache_suffix = f"_{model_name}" if model_name else ""
        cache_key = f"embedding_{self.provider.value}{cache_suffix}"

        if cache_key not in self._instances:
            kwargs = {"model_name": model_name} if model_name else {}
            if self.provider == AIProvider.GEMINI:
                from .gemini_provider import GeminiEmbeddingService

                self._instances[cache_key] = GeminiEmbeddingService(**kwargs)
            elif self.provider == AIProvider.OLLAMA:
                from .ollama_provider import OllamaEmbeddingService

                self._instances[cache_key] = OllamaEmbeddingService(**kwargs)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")

        return self._instances[cache_key]

    def get_transcription_service(self) -> BaseTranscriptionService:
        """
        Get transcription service.

        Note: Returns clear error messages if the service is unavailable.
        No silent fallback to other providers.
        """
        cache_key = f"transcription_{self.provider.value}"

        if cache_key not in self._instances:
            if self.provider == AIProvider.GEMINI:
                from .gemini_provider import GeminiTranscriptionService

                self._instances[cache_key] = GeminiTranscriptionService()
            elif self.provider == AIProvider.OLLAMA:
                from .ollama_provider import OllamaTranscriptionService

                self._instances[cache_key] = OllamaTranscriptionService()
            else:
                raise ValueError(f"Unknown provider: {self.provider}")

        return self._instances[cache_key]

    def get_completion_service(self, model_name: str | None = None) -> BaseCompletionService:
        """
        Get text completion service for configured provider.

        Args:
            model_name: Optional model to override defaults
        """
        # Include model in cache key if provided
        cache_suffix = f"_{model_name}" if model_name else ""
        cache_key = f"completion_{self.provider.value}{cache_suffix}"

        if cache_key not in self._instances:
            kwargs = {"model_name": model_name} if model_name else {}
            if self.provider == AIProvider.GEMINI:
                from .gemini_provider import GeminiCompletionService

                self._instances[cache_key] = GeminiCompletionService(**kwargs)
            elif self.provider == AIProvider.OLLAMA:
                from .ollama_provider import OllamaCompletionService

                self._instances[cache_key] = OllamaCompletionService(**kwargs)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")

        return self._instances[cache_key]

    def get_image_analysis_service(self, model_name: str | None = None) -> BaseImageAnalysisService:
        """
        Get image analysis service for configured provider.

        Args:
            model_name: Optional model to override defaults

        Note: Ollama doesn't support image analysis well. Use Gemini for this feature.
        """
        # Include model in cache key if provided
        cache_suffix = f"_{model_name}" if model_name else ""
        cache_key = f"image_analysis_{self.provider.value}{cache_suffix}"

        if cache_key not in self._instances:
            kwargs = {"model_name": model_name} if model_name else {}
            if self.provider == AIProvider.GEMINI:
                from .gemini_provider import GeminiImageAnalysisService

                self._instances[cache_key] = GeminiImageAnalysisService(**kwargs)
            elif self.provider == AIProvider.OLLAMA:
                from .ollama_provider import OllamaImageAnalysisService

                self._instances[cache_key] = OllamaImageAnalysisService(**kwargs)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")

        return self._instances[cache_key]


# Convenience functions for getting services with default provider
# Create new factory each time to respect current settings
def _get_factory() -> AIProviderFactory:
    """Get factory with current settings."""
    return AIProviderFactory()


def get_translation_service(model_name: str | None = None) -> BaseTranslationService:
    """Get translation service with default provider."""
    return _get_factory().get_translation_service(model_name=model_name)


def get_embedding_service(model_name: str | None = None) -> BaseEmbeddingService:
    """Get embedding service with default provider."""
    return _get_factory().get_embedding_service(model_name=model_name)


def get_transcription_service() -> BaseTranscriptionService:
    """Get transcription service with default provider."""
    return _get_factory().get_transcription_service()


def get_completion_service(model_name: str | None = None) -> BaseCompletionService:
    """Get completion service with default provider."""
    return _get_factory().get_completion_service(model_name=model_name)


def get_image_analysis_service(model_name: str | None = None) -> BaseImageAnalysisService:
    """Get image analysis service with default provider."""
    return _get_factory().get_image_analysis_service(model_name=model_name)
