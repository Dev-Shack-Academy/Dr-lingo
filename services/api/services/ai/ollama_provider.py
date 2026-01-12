"""
Ollama AI Provider

Implements AI services using Ollama for local LLM inference.
"""

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
from .prompts import (
    PromptVersion,
    get_completion_with_context_prompt,
    get_translation_prompt,
    get_translation_with_context_prompt,
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
                timeout=600,
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
        prompt_version: PromptVersion = PromptVersion.LATEST,
    ):
        super().__init__(prompt_version=prompt_version)
        self.client = OllamaClient(base_url)
        self.model = model_name or getattr(settings, "OLLAMA_TRANSLATION_MODEL", "granite:latest")
        self._translation_prompt = get_translation_prompt(prompt_version)
        self._translation_context_prompt = get_translation_with_context_prompt(prompt_version)

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: str = "medical",
    ) -> str:
        source_name = get_language_name(source_lang)
        target_name = get_language_name(target_lang)

        prompt = self._translation_prompt.render(
            text=text,
            source_lang=source_name,
            target_lang=target_name,
        )

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
        source_name = get_language_name(source_lang)
        target_name = get_language_name(target_lang)

        prompt = self._translation_context_prompt.render(
            text=text,
            source_lang=source_name,
            target_lang=target_name,
            conversation_history=conversation_history,
            sender_type=sender_type,
            rag_context=rag_context,
        )

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
        prompt_version: PromptVersion = PromptVersion.LATEST,
    ):
        super().__init__(prompt_version=prompt_version)
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

    def __init__(
        self,
        base_url: str | None = None,
        prompt_version: PromptVersion = PromptVersion.LATEST,
    ):
        super().__init__(prompt_version=prompt_version)
        self.client = OllamaClient(base_url)
        self._whisper_url = getattr(settings, "WHISPER_API_URL", "http://localhost:9000")

    def transcribe(
        self,
        audio_data: bytes,
        source_lang: str = "auto",
    ) -> dict[str, Any]:
        """Transcribe audio using external Whisper.cpp service."""
        if len(audio_data) < 500:
            return {
                "transcription": "",
                "detected_language": source_lang if source_lang != "auto" else "unknown",
                "success": False,
                "error": "Audio file is too small or empty",
            }

        try:
            converted_audio_data = self._convert_to_wav(audio_data)

            response = requests.post(
                f"{self._whisper_url}/inference",
                files={"file": ("audio.wav", converted_audio_data, "audio/wav")},
                data={
                    "temperature": "0.8",
                    "temperature_inc": "0.2",
                    "response_format": "json",
                    "language": source_lang if source_lang != "auto" else "",
                },
                timeout=300,
            )

            if response.status_code == 200:
                result = response.json()
                if "error" in result:
                    return {
                        "transcription": "",
                        "detected_language": "unknown",
                        "success": False,
                        "error": f"Whisper.cpp error: {result['error']}",
                    }

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
                    "error": f"Whisper.cpp endpoint not found at {self._whisper_url}/inference.",
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
                "error": f"Cannot connect to Whisper.cpp service at {self._whisper_url}.",
            }
        except requests.Timeout:
            return {
                "transcription": "",
                "detected_language": "unknown",
                "success": False,
                "error": "Whisper.cpp service timed out.",
            }
        except requests.RequestException as e:
            logger.warning(f"Whisper.cpp service error: {e}")
            return {
                "transcription": "",
                "detected_language": "unknown",
                "success": False,
                "error": f"Whisper.cpp service error: {str(e)}.",
            }

    def _convert_to_wav(self, audio_data: bytes) -> bytes:
        """Convert audio data to WAV format using ffmpeg."""
        try:
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as input_file:
                input_file.write(audio_data)
                input_path = input_file.name

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as output_file:
                output_path = output_file.name

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                input_path,
                "-ar",
                "16000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                logger.error(f"ffmpeg conversion failed: {result.stderr}")
                return audio_data

            with open(output_path, "rb") as f:
                converted_data = f.read()

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
        prompt_version: PromptVersion = PromptVersion.LATEST,
    ):
        super().__init__(prompt_version=prompt_version)
        self.client = OllamaClient(base_url)
        self.model = model_name or getattr(settings, "OLLAMA_COMPLETION_MODEL", "granite3.3:8b")
        self._completion_context_prompt = get_completion_with_context_prompt()

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
        full_prompt = self._completion_context_prompt.render(
            prompt=prompt,
            context=context,
        )
        return self.generate(full_prompt, max_tokens)
