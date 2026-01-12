"""
Prompt Management Module

Provides versioned prompts for AI services.

Structure:
- translation/     - Versioned translation prompts (v1.py, v2.py, etc.)
- completion.py    - Simple RAG completion prompts (no versioning needed)
- transcription.py - Simple transcription prompt for Gemini (no versioning needed)

Usage:
    # Translation (versioned)
    from api.services.ai.prompts import get_translation_prompt, PromptVersion
    prompt = get_translation_prompt(PromptVersion.V2)

    # Completion (simple)
    from api.services.ai.prompts import get_completion_with_context_prompt
    prompt = get_completion_with_context_prompt()
"""

from .base import BasePrompt, PromptMetadata, PromptVersion

# Completion prompts (simple, no versioning)
from .completion import (
    CompletionPrompt,
    CompletionWithContextPrompt,
    get_completion_prompt,
    get_completion_with_context_prompt,
)

# Transcription prompt (simple, no versioning - only used by Gemini)
from .transcription import (
    TranscriptionPrompt,
    get_transcription_prompt,
)

# Translation prompts (versioned - each version in its own file)
from .translation import (
    BaseTranslationPrompt,
    BaseTranslationWithContextPrompt,
    TranslationPromptV1,
    TranslationPromptV2,
    TranslationWithContextPromptV1,
    TranslationWithContextPromptV2,
    get_translation_prompt,
    get_translation_with_context_prompt,
)

__all__ = [
    # Base
    "BasePrompt",
    "PromptVersion",
    "PromptMetadata",
    # Translation (versioned)
    "BaseTranslationPrompt",
    "BaseTranslationWithContextPrompt",
    "TranslationPromptV1",
    "TranslationPromptV2",
    "TranslationWithContextPromptV1",
    "TranslationWithContextPromptV2",
    "get_translation_prompt",
    "get_translation_with_context_prompt",
    # Completion (simple)
    "CompletionPrompt",
    "CompletionWithContextPrompt",
    "get_completion_prompt",
    "get_completion_with_context_prompt",
    # Transcription (simple)
    "TranscriptionPrompt",
    "get_transcription_prompt",
]
