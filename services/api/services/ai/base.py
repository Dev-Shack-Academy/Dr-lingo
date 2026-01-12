"""
Base AI Service Classes

Provides abstract base classes for all AI services with:
- Consistent interface across providers
- Prompt management integration
- Configuration handling
"""

from abc import ABC, abstractmethod
from typing import Any

from .prompts import PromptVersion


class BaseAIService(ABC):
    """
    Abstract base class for all AI services.

    Provides common functionality:
    - Prompt version management
    - Configuration handling
    - Logging setup
    """

    def __init__(self, prompt_version: PromptVersion = PromptVersion.LATEST):
        self._prompt_version = prompt_version

    @property
    def prompt_version(self) -> PromptVersion:
        """Get the prompt version being used."""
        return self._prompt_version

    @prompt_version.setter
    def prompt_version(self, version: PromptVersion) -> None:
        """Set the prompt version to use."""
        self._prompt_version = version


class BaseTranslationService(BaseAIService):
    """Abstract base class for translation services."""

    @abstractmethod
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: str = "medical",
    ) -> str:
        """Translate text from source to target language."""
        pass

    @abstractmethod
    def translate_with_context(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        conversation_history: list[dict] | None = None,
        sender_type: str = "patient",
        rag_context: str | None = None,
    ) -> str:
        """Translate with conversation and RAG context."""
        pass


class BaseEmbeddingService(BaseAIService):
    """Abstract base class for embedding services."""

    @abstractmethod
    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text."""
        pass

    @abstractmethod
    def get_dimensions(self) -> int:
        """Return the embedding dimensions."""
        pass


class BaseTranscriptionService(BaseAIService):
    """Abstract base class for audio transcription services."""

    @abstractmethod
    def transcribe(
        self,
        audio_data: bytes,
        source_lang: str = "auto",
    ) -> dict[str, Any]:
        """
        Transcribe audio to text.

        Returns:
            dict with keys: transcription, detected_language, success, error (optional)
        """
        pass


class BaseCompletionService(BaseAIService):
    """Abstract base class for text completion/generation services."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """Generate text completion."""
        pass

    @abstractmethod
    def generate_with_context(
        self,
        prompt: str,
        context: str,
        max_tokens: int = 1000,
    ) -> str:
        """Generate completion with additional context."""
        pass
