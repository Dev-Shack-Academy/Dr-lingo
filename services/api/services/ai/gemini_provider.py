"""
Gemini AI Provider

Implements AI services using Google's Gemini API.
"""

import base64
import logging
import traceback
from typing import Any

import google.generativeai as genai
from django.conf import settings

from .base import (
    BaseCompletionService,
    BaseEmbeddingService,
    BaseTranscriptionService,
    BaseTranslationService,
)
from .prompts import (
    PromptVersion,
    get_completion_with_context_prompt,
    get_transcription_prompt,
    get_translation_prompt,
    get_translation_with_context_prompt,
)

logger = logging.getLogger(__name__)


class GeminiTranslationService(BaseTranslationService):
    """Gemini-based translation service."""

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash",
        prompt_version: PromptVersion = PromptVersion.LATEST,
    ):
        super().__init__(prompt_version=prompt_version)
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self._translation_prompt = get_translation_prompt(prompt_version)
        self._translation_context_prompt = get_translation_with_context_prompt(prompt_version)

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: str = "medical",
    ) -> str:
        prompt = self._translation_prompt.render(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
        )
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Translation failed: {str(e)}")

    def translate_with_context(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        conversation_history: list[dict] | None = None,
        sender_type: str = "patient",
        rag_context: str | None = None,
    ) -> str:
        prompt = self._translation_context_prompt.render(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            conversation_history=conversation_history,
            sender_type=sender_type,
            rag_context=rag_context,
        )
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Context-aware translation failed: {str(e)}")


class GeminiEmbeddingService(BaseEmbeddingService):
    """Gemini-based embedding service."""

    def __init__(
        self,
        model_name: str = "text-embedding-004",
        dimensions: int = 768,
        prompt_version: PromptVersion = PromptVersion.LATEST,
    ):
        super().__init__(prompt_version=prompt_version)
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        genai.configure(api_key=api_key)
        self.model_name = f"models/{model_name}"
        self.dimensions = dimensions

    def generate_embedding(self, text: str) -> list[float]:
        try:
            try:
                result = genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type="retrieval_document",
                    output_dimensionality=self.dimensions,
                )
            except TypeError:
                result = genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type="retrieval_document",
                )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    def get_dimensions(self) -> int:
        return self.dimensions


class GeminiTranscriptionService(BaseTranscriptionService):
    """Gemini-based audio transcription service."""

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash",
        prompt_version: PromptVersion = PromptVersion.LATEST,
    ):
        super().__init__(prompt_version=prompt_version)
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self._transcription_prompt = get_transcription_prompt(prompt_version)

    def transcribe(
        self,
        audio_data: bytes,
        source_lang: str = "auto",
    ) -> dict[str, Any]:
        if len(audio_data) < 500:
            return {
                "transcription": "",
                "detected_language": source_lang if source_lang != "auto" else "unknown",
                "success": False,
                "error": "Audio file is too small or empty",
            }

        prompt = self._transcription_prompt.render(source_lang=source_lang)

        try:
            audio_b64 = base64.b64encode(audio_data).decode("utf-8")
            audio_part = {"mime_type": "audio/webm", "data": audio_b64}

            response = self.model.generate_content([prompt, audio_part])
            result_text = response.text.strip()

            lines = result_text.split("\n")
            detected_lang = source_lang if source_lang != "auto" else "unknown"
            transcription = ""

            for line in lines:
                if line.startswith("LANGUAGE:"):
                    detected_lang = line.replace("LANGUAGE:", "").strip()
                elif line.startswith("TRANSCRIPTION:"):
                    transcription = line.replace("TRANSCRIPTION:", "").strip()

            if not transcription:
                transcription = result_text

            if transcription == "EMPTY_AUDIO" or detected_lang == "none":
                return {
                    "transcription": "",
                    "detected_language": source_lang if source_lang != "auto" else "unknown",
                    "success": False,
                    "error": "No speech detected",
                }

            return {
                "transcription": transcription,
                "detected_language": detected_lang,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Transcription error: {traceback.format_exc()}")
            return {
                "transcription": "",
                "detected_language": "unknown",
                "success": False,
                "error": str(e),
            }


class GeminiCompletionService(BaseCompletionService):
    """Gemini-based text completion service."""

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash",
        prompt_version: PromptVersion = PromptVersion.LATEST,
    ):
        super().__init__(prompt_version=prompt_version)
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self._completion_context_prompt = get_completion_with_context_prompt()

    def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Generation failed: {str(e)}")

    def generate_with_context(
        self,
        prompt: str,
        context: str,
        max_tokens: int = 1000,
    ) -> str:
        full_prompt = self._completion_context_prompt.render(
            prompt=prompt,
            context=context,
        )
        return self.generate(full_prompt, max_tokens)
