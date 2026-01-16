import base64
import logging
import os
import traceback
from typing import Any

import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for handling Gemini AI translation and multimodal features."""

    def __init__(self):
        """Initialize Gemini with API key from settings."""
        api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
        if not api_key or api_key == "your-gemini-api-key-here":
            raise ValueError(
                "GEMINI_API_KEY not configured. Please add your API key to services/.env file. "
                "Get your key from: https://makersuite.google.com/app/apikey"
            )

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash")
            self.vision_model = genai.GenerativeModel("gemini-2.0-flash")
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini AI: {str(e)}")

    def translate_text(self, text: str, source_lang: str, target_lang: str, context: str = "medical") -> str:
        """Translate text from source language to target language."""
        prompt = f"""
        You are a professional medical translator. Translate the following text from {source_lang} to {target_lang}.
        Before translating, you MUST perform a strict pre-check to confirm that the input text is actually written in {source_lang},
        Instead, return an error message stating: The provided text is not written in {source_lang}. Please provide text in the correct source language for translation.
        Only if the text is confidently identified as {source_lang} may you proceed with the translation
        Map all medical terms to words in that native language that explains what the doctor is trying to do or explain cause patients dont understand medical terms

        Context: {context}

        Important guidelines:
        - Maintain medical accuracy and terminology
        - Be culturally sensitive
        - Keep the tone appropriate for patient-doctor communication
        - Only return the translated text, no explanations

        Text to translate:
        {text}
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Translation failed: {str(e)}")

    def analyze_image(self, image_data: bytes, language: str = "en", context: str = "medical") -> dict[str, Any]:
        """Analyze an image and provide description in specified language."""
        prompt = f"""
        Analyze this medical image and provide:
        1. A clear description in {language}
        2. Any visible symptoms or conditions
        3. Important details a doctor should know

        Format your response as a clear, professional medical description.
        """

        try:
            response = self.vision_model.generate_content([prompt, image_data])
            return {"description": response.text.strip(), "language": language, "success": True}
        except Exception as e:
            return {"description": f"Image analysis failed: {str(e)}", "language": language, "success": False}

    def transcribe_audio(self, audio_data: bytes, source_lang: str = "auto") -> dict[str, Any]:
        """Transcribe audio using Gemini multimodal capabilities."""
        if len(audio_data) < 500:
            return {
                "transcription": "",
                "detected_language": source_lang if source_lang != "auto" else "unknown",
                "success": False,
                "error": "Audio file is too small or empty",
            }

        prompt = f"""Listen to this audio file and transcribe EXACTLY what is being said.

CRITICAL INSTRUCTIONS:
- If there is NO speech or the audio is silent/empty, respond with: "EMPTY_AUDIO"
- If there IS speech, transcribe it word-for-word
- Do NOT make up or generate content
- Only transcribe what you actually hear

{"Language: Detect automatically" if source_lang == "auto" else f"Expected language: {source_lang}"}

Respond in this format:
LANGUAGE: [2-letter code like 'en', 'es', 'ar', etc. or 'none' if empty]
TRANSCRIPTION: [exact words spoken, or "EMPTY_AUDIO" if silent]
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
                    "error": "No speech detected in audio",
                }

            return {"transcription": transcription, "detected_language": detected_lang, "success": True}

        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"Audio transcription error: {error_details}")
            return {"transcription": "", "detected_language": "unknown", "success": False, "error": str(e)}

    def translate_with_context(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        conversation_history: list = None,
        sender_type: str = "patient",
        rag_context: str = None,
    ) -> str:
        """Translate with conversation context and RAG context for better accuracy."""
        context_str = ""
        if conversation_history:
            context_str = "\n\nPrevious conversation:\n"
            for msg in conversation_history[-5:]:
                context_str += f"- {msg.get('sender_type', 'unknown')}: {msg.get('text', '')}\n"

        rag_context_str = ""
        if rag_context:
            rag_context_str = f"\n\nRELEVANT CONTEXT (Cultural & Medical):\n{rag_context}\n"

        prompt = f"""
        You are translating a {sender_type}'s message in a medical consultation.

        Translate from {source_lang} to {target_lang}.
        {context_str}
        {rag_context_str}

        Current message to translate:
        {text}

        CRITICAL TRANSLATION GUIDELINES:
        1. FORMALITY & TONE:
           - ALWAYS translate to formal, professional medical language
           - Maintain respectful, professional tone appropriate for medical consultations

        2. CULTURAL RESTRICTIONS:
           - Strictly follow cultural guidelines from the RAG context above
           - Adapt language to respect cultural sensitivities

        3. MEDICAL ACCURACY:
           - Maintain precise medical terminology
           - Ensure clarity for patient safety

        4. OUTPUT:
           - Return ONLY the translated text
           - No explanations, notes, or metadata
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Context-aware translation failed: {str(e)}")


# Singleton instance
_gemini_service = None


def get_gemini_service() -> GeminiService:
    """Get or create Gemini service instance."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
