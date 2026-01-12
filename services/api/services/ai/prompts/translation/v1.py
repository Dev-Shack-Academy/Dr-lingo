"""
Translation Prompts V1

Original translation prompts for medical translation.
"""

from typing import Any

from ..base import PromptMetadata, PromptVersion
from .base import BaseTranslationPrompt, BaseTranslationWithContextPrompt


class TranslationPromptV1(BaseTranslationPrompt):
    """
    Version 1 of the basic translation prompt.

    Simple, direct translation prompt for medical contexts.
    """

    def _get_metadata(self) -> PromptMetadata:
        return PromptMetadata(
            version=PromptVersion.V1,
            name="translation_basic",
            description="Basic medical translation prompt",
            tags=["translation", "medical"],
        )

    def render(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **kwargs: Any,
    ) -> str:
        return f"""System:
You are a professional medical translator. Translate accurately while being culturally sensitive.
Map medical terms to understandable language for patients.
Return ONLY the translated text, no explanations.

User:
Translate from {source_lang} to {target_lang}:
{text}

A:
"""


class TranslationWithContextPromptV1(BaseTranslationWithContextPrompt):
    """
    Version 1 of the context-aware translation prompt.

    Includes conversation history and RAG context for better translations.
    """

    def _get_metadata(self) -> PromptMetadata:
        return PromptMetadata(
            version=PromptVersion.V1,
            name="translation_with_context",
            description="Context-aware medical translation with RAG support",
            tags=["translation", "medical", "rag", "context"],
        )

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
        # Build conversation history string
        context_str = ""
        if conversation_history:
            context_str = "Previous conversation:\n"
            for msg in conversation_history[-5:]:
                context_str += f"- {msg.get('sender_type', 'unknown')}: {msg.get('text', '')}\n"

        # Build RAG context string
        rag_str = ""
        if rag_context:
            rag_str = f"### Reference Information\n{rag_context}\n"

        return f"""System:
You are an expert medical translator specializing in {target_lang}.
Your goal is to provide accurate, culturally respectful translations for a {sender_type}.

CRITICAL INSTRUCTIONS:
1. Use the "Reference Information" below as your primary source of truth for terminology, grammar rules, and linguistic style.
2. The Reference Information contains natural spoken language examples and transcriptions. Use them to infer correct {target_lang} phrasing, noun class usage, and cultural tone.
3. If the Reference Information contains specific noun class rules, APPLY THEM STRICTLY.
4. Do not transliterate. Prioritize natural, idiomatic {target_lang} as shown in the examples.
5. Return ONLY the translated text.

User:
{rag_str}

### Conversation History
{context_str}

### Task
Translate the following text from {source_lang} to {target_lang}:
"{text}"

A:
"""
