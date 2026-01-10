import logging
import os
import subprocess
import tempfile
from typing import Any

import requests
from django.conf import settings

from api.utils import get_language_name

from .base import (
    BaseCompletionService,
    BaseEmbeddingService,
    BaseTranscriptionService,
    BaseTranslationService,
)

logger = logging.getLogger(__name__)


class OllamaClient:
    """Base client for Ollama API calls."""

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")

    def generate(self, model: str, prompt: str, **kwargs) -> str:
        """Generate text using Ollama."""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    **kwargs,
                },
                timeout=600,
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.RequestException as e:
            logger.error(f"Ollama generate error: {e}")
            raise Exception(f"Ollama API error: {str(e)}")

    def embeddings(self, model: str, prompt: str) -> list[float]:
        """Generate embeddings using Ollama."""
        try:
            logger.info(f"Generating embedding with model {model} for text: {prompt[:50]}...")
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": model, "prompt": prompt},
                timeout=600,  # Increased timeout for first load
            )
            response.raise_for_status()
            embedding = response.json().get("embedding", [])
            logger.info(f"Embedding generated successfully, dimensions: {len(embedding)}")
            return embedding
        except requests.Timeout:
            logger.error("Ollama embeddings timeout - model may be loading")
            raise Exception("Ollama timeout - model may still be loading. Try again.")
        except requests.RequestException as e:
            logger.error(f"Ollama embeddings error: {e}")
            raise Exception(f"Ollama API error: {str(e)}")

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False


class OllamaTranslationService(BaseTranslationService):
    """Ollama-based translation service using Granite or similar models."""

    def __init__(
        self,
        model_name: str | None = None,
        base_url: str | None = None,
    ):
        self.client = OllamaClient(base_url)
        self.model = model_name or getattr(settings, "OLLAMA_TRANSLATION_MODEL", "granite:latest")

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: str = "medical",
    ) -> str:
        # Convert language codes to full names for better LLM understanding
        source_name = get_language_name(source_lang)
        target_name = get_language_name(target_lang)

        prompt = f"""System:
You are a professional medical translator. Translate accurately while being culturally sensitive.
Map medical terms to understandable language for patients.
Return ONLY the translated text, no explanations.

User:
Translate from {source_name} to {target_name}:
{text}

Assistant:
"""

        result = self.client.generate(self.model, prompt)
        return result.strip()

    def translate_with_context(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        conversation_history: list[dict] | None = None,
        sender_type: str = "patient",
        rag_context: str | None = None,
    ) -> str:
        # Convert language codes to full names for better LLM understanding
        source_name = get_language_name(source_lang)
        target_name = get_language_name(target_lang)

        context_str = ""
        if conversation_history:
            context_str = "Previous conversation:\n"
            for msg in conversation_history[-5:]:
                context_str += f"- {msg.get('sender_type', 'unknown')}: {msg.get('text', '')}\n"

        rag_str = ""
        if rag_context:
            rag_str = f"### Reference Information\n{rag_context}\n"

        prompt = f"""System:
You are an expert medical translator specializing in {target_name}.
Your goal is to provide accurate, culturally respectful translations for a {sender_type}.

CRITICAL INSTRUCTIONS:
1. Use the "Reference Information" below as your primary source of truth for terminology, grammar rules, and linguistic style.
2. The Reference Information contains natural spoken language examples and transcriptions. Use them to infer correct {target_name} phrasing, noun class usage, and cultural tone.
3. If the Reference Information contains specific noun class rules, APPLY THEM STRICTLY.
4. Do not transliterate. Prioritize natural, idiomatic {target_name} as shown in the examples.
5. Return ONLY the translated text.

User:
{rag_str}

### Conversation History
{context_str}

### Task
Translate the following text from {source_name} to {target_name}:
"{text}"

Assistant:
"""
        logger.debug(f"Translation Prompt:\n{prompt}")

        result = self.client.generate(self.model, prompt)
        return result.strip()


class OllamaEmbeddingService(BaseEmbeddingService):
    """Ollama-based embedding service using nomic-embed-text or similar."""

    def __init__(
        self,
        model_name: str | None = None,
        base_url: str | None = None,
        dimensions: int = 768,
    ):
        self.client = OllamaClient(base_url)
        self.model = model_name or getattr(settings, "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:latest")
        self._dimensions = dimensions

    def generate_embedding(self, text: str) -> list[float]:
        return self.client.embeddings(self.model, text)

    def get_dimensions(self) -> int:
        return self._dimensions


class OllamaTranscriptionService(BaseTranscriptionService):
    """
    Ollama-based transcription service using Whisper.cpp.

    Note: Ollama doesn't natively support audio transcription.
    This implementation uses Whisper.cpp via external Docker service.
    """

    def __init__(self, base_url: str | None = None):
        self.client = OllamaClient(base_url)
        self._whisper_url = getattr(settings, "WHISPER_API_URL", "http://localhost:9000")

    def transcribe(
        self,
        audio_data: bytes,
        source_lang: str = "auto",
    ) -> dict[str, Any]:
        """
        Transcribe audio using external Whisper.cpp service.

        Uses the correct Whisper.cpp API endpoints:
        - /inference for transcription
        - /load for model loading (if needed)

        Converts WebM/Opus to WAV format since Whisper.cpp doesn't handle WebM well.

        Returns clear error messages if the service is unavailable.
        """
        if len(audio_data) < 500:
            return {
                "transcription": "",
                "detected_language": source_lang if source_lang != "auto" else "unknown",
                "success": False,
                "error": "Audio file is too small or empty",
            }

        try:
            # Convert audio to WAV format for better Whisper.cpp compatibility
            converted_audio_data = self._convert_to_wav(audio_data)

            # Use the correct Whisper.cpp endpoint: /inference
            response = requests.post(
                f"{self._whisper_url}/inference",
                files={"file": ("audio.wav", converted_audio_data, "audio/wav")},
                data={
                    "temperature": "0.8",  # Use higher temperature for better detection
                    "temperature_inc": "0.2",
                    "response_format": "json",
                    "language": source_lang if source_lang != "auto" else "",
                },
                timeout=300,  # Increased timeout to 5 minutes for complex audio
            )

            if response.status_code == 200:
                result = response.json()

                # Check for Whisper.cpp errors
                if "error" in result:
                    return {
                        "transcription": "",
                        "detected_language": "unknown",
                        "success": False,
                        "error": f"Whisper.cpp error: {result['error']}",
                    }

                # Whisper.cpp returns text in 'text' field
                transcription = result.get("text", "").strip()
                detected_lang = result.get("language", source_lang)

                return {
                    "transcription": transcription,
                    "detected_language": detected_lang,
                    "success": True,
                }
            elif response.status_code == 404:
                return {
                    "transcription": "",
                    "detected_language": "unknown",
                    "success": False,
                    "error": (
                        f"Whisper.cpp endpoint not found at {self._whisper_url}/inference. "
                        f"Please ensure Whisper.cpp server is running with: docker-compose up whisper -d"
                    ),
                }
            else:
                return {
                    "transcription": "",
                    "detected_language": "unknown",
                    "success": False,
                    "error": f"Whisper.cpp API error: {response.status_code} - {response.text}",
                }

        except requests.ConnectionError:
            return {
                "transcription": "",
                "detected_language": "unknown",
                "success": False,
                "error": (
                    f"Cannot connect to Whisper.cpp service at {self._whisper_url}. "
                    f"Please start the service with: docker-compose up whisper -d"
                ),
            }
        except requests.Timeout:
            return {
                "transcription": "",
                "detected_language": "unknown",
                "success": False,
                "error": (
                    "Whisper.cpp service timed out. The audio may be too long or the service is overloaded. "
                    "Try with shorter audio or restart the service: docker-compose restart whisper"
                ),
            }
        except requests.RequestException as e:
            logger.warning(f"Whisper.cpp service error: {e}")
            return {
                "transcription": "",
                "detected_language": "unknown",
                "success": False,
                "error": (
                    f"Whisper.cpp service error: {str(e)}. " f"Try starting the service: docker-compose up whisper -d"
                ),
            }

    def _convert_to_wav(self, audio_data: bytes) -> bytes:
        """
        Convert audio data to WAV format using ffmpeg.

        Whisper.cpp works better with WAV format than WebM/Opus.
        """
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as input_file:
                input_file.write(audio_data)
                input_path = input_file.name

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as output_file:
                output_path = output_file.name

            # Convert using ffmpeg
            cmd = [
                "ffmpeg",
                "-y",  # -y to overwrite output file
                "-i",
                input_path,
                "-ar",
                "16000",  # 16kHz sample rate (good for speech)
                "-ac",
                "1",  # Mono
                "-c:a",
                "pcm_s16le",  # 16-bit PCM
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                logger.error(f"ffmpeg conversion failed: {result.stderr}")
                # Return original data if conversion fails
                return audio_data

            # Read converted audio
            with open(output_path, "rb") as f:
                converted_data = f.read()

            # Clean up temporary files
            try:
                os.unlink(input_path)
                os.unlink(output_path)
            except (OSError, FileNotFoundError):
                pass

            logger.info(f"Audio converted: {len(audio_data)} bytes -> {len(converted_data)} bytes")
            return converted_data

        except subprocess.TimeoutExpired:
            logger.error("ffmpeg conversion timed out")
            return audio_data
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            return audio_data


class OllamaCompletionService(BaseCompletionService):
    """Ollama-based text completion service."""

    def __init__(
        self,
        model_name: str | None = None,
        base_url: str | None = None,
    ):
        self.client = OllamaClient(base_url)
        self.model = model_name or getattr(settings, "OLLAMA_COMPLETION_MODEL", "granite3.3:8b")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        return self.client.generate(
            self.model,
            prompt,
            options={"num_predict": max_tokens, "temperature": temperature},
        )

    def generate_with_context(
        self,
        prompt: str,
        context: str,
        max_tokens: int = 1000,
    ) -> str:
        full_prompt = f"""System:
Use the following context to answer the question.

User:
Context:
{context}

Question:
{prompt}

Assistant:
"""
        return self.generate(full_prompt, max_tokens)
