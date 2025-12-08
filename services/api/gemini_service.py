"""
Gemini AI service for translation and multimodal processing.

This service handles:
- Real-time translation between languages
- Image understanding and description
- Context-aware medical translation
- Multimodal content processing
"""

import os
from typing import Any, Dict

import google.generativeai as genai
from django.conf import settings


class GeminiTranslationService:
    """
    Service for handling Gemini AI translation and multimodal features.
    """

    def __init__(self):
        """Initialize Gemini with API key from settings."""
        api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or settings")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.vision_model = genai.GenerativeModel("gemini-1.5-flash")

    def translate_text(self, text: str, source_lang: str, target_lang: str, context: str = "medical") -> str:
        """
        Translate text from source language to target language.

        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'en', 'es', 'fr')
            target_lang: Target language code
            context: Context for translation (medical, general, etc.)

        Returns:
            Translated text
        """
        prompt = f"""
        You are a professional medical translator. Translate the following text from {source_lang} to {target_lang}.

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

    def analyze_image(self, image_data: bytes, language: str = "en", context: str = "medical") -> Dict[str, Any]:
        """
        Analyze an image and provide description in specified language.

        Args:
            image_data: Image bytes
            language: Language for description
            context: Context for analysis

        Returns:
            Dictionary with description and analysis
        """
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

    def translate_with_context(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        conversation_history: list = None,
        sender_type: str = "patient",
    ) -> str:
        """
        Translate with conversation context for better accuracy.

        Args:
            text: Text to translate
            source_lang: Source language
            target_lang: Target language
            conversation_history: Previous messages for context
            sender_type: 'patient' or 'doctor'

        Returns:
            Translated text with context awareness
        """
        context_str = ""
        if conversation_history:
            context_str = "\n\nPrevious conversation:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages
                context_str += f"- {msg.get('sender_type', 'unknown')}: {msg.get('text', '')}\n"

        prompt = f"""
        You are translating a {sender_type}'s message in a medical consultation.

        Translate from {source_lang} to {target_lang}.
        {context_str}

        Current message to translate:
        {text}

        Guidelines:
        - Maintain medical terminology accuracy
        - Consider the conversation context
        - Use appropriate formality for {sender_type}
        - Only return the translation, no explanations
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Context-aware translation failed: {str(e)}")


# Singleton instance
_gemini_service = None


def get_gemini_service() -> GeminiTranslationService:
    """Get or create Gemini service instance."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiTranslationService()
    return _gemini_service
