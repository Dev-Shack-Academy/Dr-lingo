"""
Transcription Prompts

Simple prompt for Gemini multimodal audio transcription.
Note: Whisper.cpp uses direct API calls with parameters - not prompts.

This doesn't need versioning - it's a simple "transcribe this audio" instruction.
"""

from typing import Any

from .base import BasePrompt, PromptMetadata, PromptVersion


class TranscriptionPrompt(BasePrompt):
    """
    Transcription prompt for Gemini multimodal.

    Used when transcribing audio with Gemini's multimodal capabilities.
    Whisper.cpp doesn't use this - it has its own API parameters.
    """

    def _get_metadata(self) -> PromptMetadata:
        return PromptMetadata(
            version=PromptVersion.V1,
            name="transcription",
            description="Audio transcription prompt for Gemini multimodal",
            tags=["transcription", "audio", "speech-to-text"],
        )

    def render(self, source_lang: str = "auto", **kwargs: Any) -> str:
        if source_lang == "auto":
            lang_instruction = "Detect the language automatically."
        else:
            lang_instruction = f"Expected language: {source_lang}"

        return f"""<|system|>
You are a medical transcription specialist. Transcribe the audio exactly as spoken.

RULES:
1. Transcribe word-for-word what is said
2. If no speech or silent audio, respond: EMPTY_AUDIO
3. Preserve medical terminology exactly
4. Do NOT make up or hallucinate content

{lang_instruction}
<|end|>

<|user|>
Transcribe the audio. If silent, respond: EMPTY_AUDIO
<|end|>

<|assistant|>
"""


def get_transcription_prompt(source_lang: str = "auto") -> TranscriptionPrompt:
    """Get the transcription prompt."""
    return TranscriptionPrompt()
