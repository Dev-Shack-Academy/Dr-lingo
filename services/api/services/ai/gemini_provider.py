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

logger = logging.getLogger(__name__)


class GeminiTranslationService(BaseTranslationService):
    """Gemini-based translation service."""

    def __init__(self, model_name: str = "gemini-2.0-flash"):
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: str = "medical",
    ) -> str:
        prompt = f"""
You are a professional medical translator. Translate from {source_lang} to {target_lang}.

Context: {context}

Guidelines:
- Maintain medical accuracy
- Be culturally sensitive
- Use appropriate tone for patient-doctor communication
- Map medical terms to understandable language for patients
- Return ONLY the translated text

Text to translate:
{text}
"""
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
        context_str = ""
        if conversation_history:
            context_str = "\n\nPrevious conversation:\n"
            for msg in conversation_history[-5:]:
                context_str += f"- {msg.get('sender_type', 'unknown')}: {msg.get('text', '')}\n"

        rag_context_str = ""
        if rag_context:
            rag_context_str = f"\n\nCultural & Medical Context:\n{rag_context}\n"

        prompt = f"""
You are translating a {sender_type}'s message in a medical consultation.
Translate from {source_lang} to {target_lang}.
{context_str}
{rag_context_str}

Message to translate:
{text}

Guidelines:
1. Use formal, professional medical language
2. Follow cultural guidelines from context
3. Maintain medical accuracy
4. Return ONLY the translated text
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Context-aware translation failed: {str(e)}")


class GeminiEmbeddingService(BaseEmbeddingService):
    """Gemini-based embedding service."""

    def __init__(self, model_name: str = "text-embedding-004", dimensions: int = 768):
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

    def __init__(self, model_name: str = "gemini-2.0-flash"):
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

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

        prompt = f"""Listen to this audio and transcribe EXACTLY what is said.

Instructions:
- If NO speech or silent, respond: "EMPTY_AUDIO"
- If speech exists, transcribe word-for-word
- Do NOT make up content

{"Language: Detect automatically" if source_lang == "auto" else f"Expected language: {source_lang}"}

Format:
LANGUAGE: [2-letter code or 'none']
TRANSCRIPTION: [exact words or "EMPTY_AUDIO"]
"""
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

    def __init__(self, model_name: str = "gemini-2.0-flash"):
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

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
        full_prompt = f"""Context:
{context}

Question/Task:
{prompt}

Answer:"""
        return self.generate(full_prompt, max_tokens)
