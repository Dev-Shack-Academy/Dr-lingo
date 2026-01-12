"""
Translation Prompts V2

Improved translation prompts optimized for:
- South African languages (Zulu, Xhosa, Sotho, Tswana, Afrikaans)
- Medical terminology accuracy
- Noun class handling for Bantu languages
- Better RAG context integration with structured sections
- Role-aware translation (doctor vs patient)
"""

from typing import Any

from ..base import PromptMetadata, PromptVersion
from .base import BaseTranslationPrompt, BaseTranslationWithContextPrompt

# South African language codes and their noun class info
SA_BANTU_LANGUAGES = {
    "zu": "Zulu",
    "xh": "Xhosa",
    "st": "Sotho",
    "tn": "Tswana",
    "ts": "Tsonga",
    "ss": "Swati",
    "ve": "Venda",
    "nr": "Ndebele",
}

NOUN_CLASS_LANGUAGES = {"zu", "xh", "st", "tn", "ts", "ss", "ve", "nr"}


def _get_language_specific_rules(target_lang: str) -> str:
    """Get language-specific translation rules."""
    lang_code = target_lang.lower()[:2] if len(target_lang) >= 2 else target_lang.lower()

    if lang_code in NOUN_CLASS_LANGUAGES:
        return """BANTU LANGUAGE RULES (CRITICAL):
- Apply correct noun class prefixes (umu-, aba-, um-, imi-, etc.)
- Maintain concordial agreement throughout the sentence
- Use appropriate subject and object concords
- Respect honorific forms when addressing elders or authority figures
- Medical terms: Use established Zulu/Xhosa medical vocabulary where it exists"""

    elif lang_code == "af":
        return """AFRIKAANS RULES:
- Use formal register for medical contexts
- Maintain correct word order (verb-second in main clauses)
- Use appropriate medical terminology from Afrikaans medical literature"""

    return """GENERAL RULES:
- Maintain natural word order for the target language
- Use appropriate register (formal for medical contexts)"""


class TranslationPromptV2(BaseTranslationPrompt):
    """
    Version 2 of the translation prompt.

    Improvements over V1:
    - Chat format with clear system/user/assistant tags
    - Explicit medical interpreter role
    - Language-specific rules for South African languages
    - Cultural sensitivity guidelines
    - Better output format instructions
    """

    def _get_metadata(self) -> PromptMetadata:
        return PromptMetadata(
            version=PromptVersion.V2,
            name="translation_basic_v2",
            description="Improved medical translation with chain-of-thought",
            tags=["translation", "medical", "v2", "south-african"],
        )

    def render(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **kwargs: Any,
    ) -> str:
        lang_rules = _get_language_specific_rules(target_lang)

        return f"""<|system|>
You are a certified medical interpreter specializing in South African healthcare communication.

ROLE: Translate medical conversations between healthcare providers and patients.
LANGUAGES: {source_lang} → {target_lang}

CORE PRINCIPLES:
1. ACCURACY: Preserve exact medical meaning. Never add, omit, or modify clinical information.
2. CLARITY: Use simple, clear language appropriate for patients. Avoid jargon unless the original uses it.
3. CULTURAL SENSITIVITY: Adapt expressions to be culturally appropriate while maintaining meaning.
4. TONE: Match the original tone (formal/informal, urgent/calm).

{lang_rules}

MEDICAL TERMINOLOGY:
- Preserve drug names exactly (e.g., "paracetamol" stays "paracetamol")
- For conditions, use the {target_lang} term if widely known, otherwise keep English with explanation
- Dosage instructions must be precise and unambiguous

OUTPUT: Provide ONLY the translated text. No explanations, notes, or alternatives.
<|end|>

<|user|>
Translate to {target_lang}:
{text}
<|end|>

<|assistant|>
"""


class TranslationWithContextPromptV2(BaseTranslationWithContextPrompt):
    """
    Version 2 of the context-aware translation prompt.

    Improvements over V1:
    - Structured RAG context with clear sections
    - Language-specific rules for Bantu languages
    - Role-aware translation (doctor vs patient language)
    - Better handling of knowledge base vs patient context
    - Explicit instructions for using reference materials
    """

    def _get_metadata(self) -> PromptMetadata:
        return PromptMetadata(
            version=PromptVersion.V2,
            name="translation_with_context_v2",
            description="Enhanced context-aware medical translation",
            tags=["translation", "medical", "rag", "context", "v2"],
        )

    def _format_rag_context(self, rag_context: str | None) -> str:
        """Format RAG context with clear structure."""
        if not rag_context:
            return ""

        return f"""<reference_materials>
USE THESE MATERIALS AS YOUR PRIMARY GUIDE for:
- Correct terminology and phrasing in the target language
- Grammar patterns and noun class usage
- Cultural expressions and honorifics
- Medical vocabulary translations

{rag_context}
</reference_materials>

"""

    def _format_conversation_history(self, history: list[dict] | None) -> str:
        """Format conversation history for context."""
        if not history or len(history) == 0:
            return ""

        lines = ["<conversation_history>"]
        for msg in history[-5:]:  # Last 5 messages
            role = msg.get("sender_type", "unknown").upper()
            text = msg.get("text", "")
            lines.append(f"[{role}]: {text}")
        lines.append("</conversation_history>")

        return "\n".join(lines) + "\n\n"

    def _get_role_instruction(self, sender_type: str) -> str:
        """Get role-specific translation guidance."""
        if sender_type == "doctor":
            return """SPEAKER: HEALTHCARE PROVIDER
- Use professional but accessible language
- Medical terms should be precise
- Instructions should be clear and actionable
- Maintain authority while being approachable"""
        else:
            return """SPEAKER: PATIENT
- Use warm, natural conversational language
- Symptoms and concerns should be expressed naturally
- Respect cultural ways of describing illness
- Preserve emotional tone (worry, relief, confusion)"""

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
        # Build sections
        rag_section = self._format_rag_context(rag_context)
        conv_section = self._format_conversation_history(conversation_history)
        role_instruction = self._get_role_instruction(sender_type)
        lang_rules = _get_language_specific_rules(target_lang)

        return f"""<|system|>
You are an expert medical interpreter for {target_lang}, specializing in South African healthcare contexts.

TASK: Translate the message while maintaining medical accuracy and cultural appropriateness.

{role_instruction}

TRANSLATION RULES:
1. MEDICAL ACCURACY: Never alter clinical meaning. Symptoms, dosages, and instructions must be exact.
2. NATURAL LANGUAGE: Produce fluent, natural {target_lang}. Avoid word-for-word translation.
3. REFERENCE FIRST: If reference materials are provided, use them as your PRIMARY guide for terminology and phrasing.
4. CULTURAL ADAPTATION: Use culturally appropriate greetings, honorifics, and expressions.

{lang_rules}

CRITICAL: If the reference materials show how to express something in {target_lang}, USE THAT PHRASING.
The reference materials contain real examples of natural {target_lang} speech.

OUTPUT: Return ONLY the translated text. No explanations, alternatives, or notes.
<|end|>

<|user|>
{rag_section}{conv_section}<message_to_translate>
{text}
</message_to_translate>

Translate the above message from {source_lang} to {target_lang}.
<|end|>

<|assistant|>
"""
