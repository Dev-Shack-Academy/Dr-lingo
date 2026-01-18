"""
Translation Prompts Module

Versioned prompts for medical translation tasks.
Each version is in its own file for better tracking and readability.

Usage:
    from api.services.ai.prompts.translation import (
        get_translation_prompt,
        get_translation_with_context_prompt,
        TranslationPromptV1,
        TranslationPromptV2,
    )
"""

from ..base import PromptVersion
from .base import BaseTranslationPrompt, BaseTranslationWithContextPrompt
from .v1 import TranslationPromptV1, TranslationWithContextPromptV1
from .v2 import TranslationPromptV2, TranslationWithContextPromptV2

# Registry - Update LATEST here when adding new versions


_TRANSLATION_PROMPTS: dict[PromptVersion, type[BaseTranslationPrompt]] = {
    PromptVersion.V1: TranslationPromptV1,
    PromptVersion.V2: TranslationPromptV2,
    PromptVersion.LATEST: TranslationPromptV2,
}

_TRANSLATION_WITH_CONTEXT_PROMPTS: dict[PromptVersion, type[BaseTranslationWithContextPrompt]] = {
    PromptVersion.V1: TranslationWithContextPromptV1,
    PromptVersion.V2: TranslationWithContextPromptV2,
    PromptVersion.LATEST: TranslationWithContextPromptV2,
}


def get_translation_prompt(version: PromptVersion = PromptVersion.LATEST) -> BaseTranslationPrompt:
    """Get a translation prompt by version."""
    prompt_class = _TRANSLATION_PROMPTS.get(version)
    if not prompt_class:
        raise ValueError(f"Unknown translation prompt version: {version}")
    return prompt_class()


def get_translation_with_context_prompt(
    version: PromptVersion = PromptVersion.LATEST,
) -> BaseTranslationWithContextPrompt:
    """Get a context-aware translation prompt by version."""
    prompt_class = _TRANSLATION_WITH_CONTEXT_PROMPTS.get(version)
    if not prompt_class:
        raise ValueError(f"Unknown translation with context prompt version: {version}")
    return prompt_class()


__all__ = [
    # Base classes
    "BaseTranslationPrompt",
    "BaseTranslationWithContextPrompt",
    # V1
    "TranslationPromptV1",
    "TranslationWithContextPromptV1",
    # V2
    "TranslationPromptV2",
    "TranslationWithContextPromptV2",
    # Factory functions
    "get_translation_prompt",
    "get_translation_with_context_prompt",
]
