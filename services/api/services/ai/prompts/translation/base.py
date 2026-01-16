"""
Base Translation Prompt Classes

Abstract base classes that all translation prompt versions must inherit from.
"""

from abc import abstractmethod
from typing import Any

from ..base import BasePrompt


class BaseTranslationPrompt(BasePrompt):
    """Base class for basic translation prompts."""

    @abstractmethod
    def render(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **kwargs: Any,
    ) -> str:
        """
        Render translation prompt.

        Args:
            text: Text to translate
            source_lang: Source language name
            target_lang: Target language name

        Returns:
            Rendered prompt string
        """
        pass


class BaseTranslationWithContextPrompt(BasePrompt):
    """Base class for context-aware translation prompts."""

    @abstractmethod
    def render(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        conversation_history: list[dict] | None = None,
        sender_type: str = "patient",
        rag_context: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Render translation prompt with context.

        Args:
            text: Text to translate
            source_lang: Source language name
            target_lang: Target language name
            conversation_history: Previous messages in conversation
            sender_type: Who is speaking ("doctor" or "patient")
            rag_context: Retrieved context from knowledge base

        Returns:
            Rendered prompt string
        """
        pass
