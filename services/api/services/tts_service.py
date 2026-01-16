import logging
import os
import wave

from django.conf import settings

logger = logging.getLogger(__name__)

# Global model cache - one model per voice
_piper_voices: dict = {}

# Piper models directory
PIPER_MODELS_DIR = os.path.join(settings.BASE_DIR, "media", "piper_models")

# Language to Piper voice mapping
# Format: language_code -> (voice_name, is_native)
# Native voices have proper pronunciation, fallback uses English voice
PIPER_VOICE_MAP = {
    # Major languages with quality voices
    "en": ("en_US-lessac-medium", True),
    "eng": ("en_US-lessac-medium", True),
    "es": ("es_ES-sharvard-medium", True),
    "spa": ("es_ES-sharvard-medium", True),
    "fr": ("fr_FR-siwis-medium", True),
    "fra": ("fr_FR-siwis-medium", True),
    "de": ("de_DE-thorsten-medium", True),
    "deu": ("de_DE-thorsten-medium", True),
    "pt": ("pt_BR-faber-medium", True),
    "por": ("pt_BR-faber-medium", True),
    "it": ("it_IT-riccardo-x_low", True),
    "ita": ("it_IT-riccardo-x_low", True),
    "pl": ("pl_PL-darkman-medium", True),
    "pol": ("pl_PL-darkman-medium", True),
    "nl": ("nl_NL-mls-medium", True),
    "nld": ("nl_NL-mls-medium", True),
    "ru": ("ru_RU-ruslan-medium", True),
    "rus": ("ru_RU-ruslan-medium", True),
    "zh": ("zh_CN-huayan-medium", True),
    "zho": ("zh_CN-huayan-medium", True),
    # South African languages - fallback to English (Piper doesn't have native voices yet)
    "afr": ("en_US-lessac-medium", False),  # Afrikaans - no native voice, fallback to English
    "zul": ("en_US-lessac-medium", False),  # isiZulu
    "xho": ("en_US-lessac-medium", False),  # isiXhosa
    "sot": ("en_US-lessac-medium", False),  # Sesotho
    "nso": ("en_US-lessac-medium", False),  # Sepedi
    "tsn": ("en_US-lessac-medium", False),  # Setswana
    "ssw": ("en_US-lessac-medium", False),  # siSwati
    "ven": ("en_US-lessac-medium", False),  # Tshivenda
    "tso": ("en_US-lessac-medium", False),  # Xitsonga
    "nbl": ("en_US-lessac-medium", False),  # isiNdebele
}

# Default voice for unknown languages
DEFAULT_VOICE = "en_US-lessac-medium"


def get_piper_voice(language: str):
    """
    Get or load Piper voice model for a language.
    Models are lazy-loaded and cached globally.

    Args:
        language: ISO 639-3 language code (e.g., 'en', 'es', 'zul')

    Returns:
        PiperVoice: Loaded voice model
    """
    from piper import PiperVoice

    # Map language to voice model
    voice_info = PIPER_VOICE_MAP.get(language.lower(), (DEFAULT_VOICE, False))
    voice_name = voice_info[0]

    # Return cached model if available
    if voice_name in _piper_voices:
        logger.debug(f"Using cached Piper voice: {voice_name}")
        return _piper_voices[voice_name]

    # Load new model
    logger.info(f"Loading Piper voice: {voice_name} for language: {language}")
    try:
        # Build full path to model file
        model_path = os.path.join(PIPER_MODELS_DIR, f"{voice_name}.onnx")
        config_path = os.path.join(PIPER_MODELS_DIR, f"{voice_name}.onnx.json")

        # Check if model exists locally
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Piper voice model not found: {model_path}\n"
                f"Download it from: https://huggingface.co/rhasspy/piper-voices\n"
                f"Place .onnx and .onnx.json files in: {PIPER_MODELS_DIR}"
            )

        voice = PiperVoice.load(model_path, config_path=config_path, use_cuda=False)
        _piper_voices[voice_name] = voice
        logger.info(f"Successfully loaded Piper voice: {voice_name}")
        return voice

    except Exception as e:
        logger.error(f"Failed to load Piper voice {voice_name}: {e}")
        # Fallback to English if specific voice fails
        if voice_name != DEFAULT_VOICE:
            logger.warning("Falling back to English voice")
            return get_piper_voice("en")
        raise


def text_to_speech(
    text: str,
    language: str,
    speaker_wav: str = None,
    speaker_type: str = None,
    output_path: str = None,
    speed: float = 1.0,
) -> dict:
    """
    Convert text to speech using Piper TTS.

    Args:
        text: Text to synthesize
        language: ISO 639-3 language code
        speaker_wav: Not used (Piper doesn't support voice cloning)
        speaker_type: Not used (Piper uses single voice per model)
        output_path: Path to save WAV file
        speed: Speech speed multiplier (length_scale: 1.0=normal, <1=faster, >1=slower)

    Returns:
        dict: {
            "success": bool,
            "file_path": str,
            "file_size": int,
            "language": str,
            "error": str (if failed)
        }
    """
    try:
        # Validate text
        if not text or not text.strip():
            logger.warning("Empty text provided for TTS")
            return {"success": False, "error": "Empty text provided"}

        # Get voice for language
        voice = get_piper_voice(language)

        # Generate output path if not provided
        if output_path is None:
            import tempfile

            output_path = tempfile.mktemp(suffix=".wav")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        logger.info(f"Generating TTS for language '{language}': {text[:50]}...")

        # Synthesize speech to WAV file
        with wave.open(output_path, "wb") as wav_file:
            # Set WAV parameters
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(voice.config.sample_rate)

            # Generate and write audio chunks
            for chunk in voice.synthesize(text):
                wav_file.writeframes(chunk.audio_int16_bytes)

        # Get file info
        file_size = os.path.getsize(output_path)

        # Get voice info for logging
        voice_info = PIPER_VOICE_MAP.get(language.lower(), (DEFAULT_VOICE, False))
        is_native = voice_info[1]

        logger.info(
            f"TTS generated successfully: {output_path} "
            f"({file_size / 1024:.1f} KB, {len(text)} chars, "
            f"native={is_native})"
        )

        return {
            "success": True,
            "file_path": output_path,
            "file_size": file_size,
            "language": language,
            "is_native_voice": is_native,
        }

    except Exception as e:
        logger.error(f"TTS generation failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


def is_tts_available() -> bool:
    """Check if TTS service is available."""
    try:
        import importlib.util

        if importlib.util.find_spec("piper") is None:
            logger.warning("Piper TTS module not installed")
            return False

        # Also check if models directory exists and has models
        if not os.path.exists(PIPER_MODELS_DIR):
            logger.warning(f"Piper models directory not found: {PIPER_MODELS_DIR}")
            return False

        # Check for at least one .onnx model file
        model_files = [f for f in os.listdir(PIPER_MODELS_DIR) if f.endswith(".onnx")]
        if not model_files:
            logger.warning(f"No Piper voice models found in: {PIPER_MODELS_DIR}")
            return False

        logger.debug(f"Piper TTS available with {len(model_files)} voice models")
        return True

    except Exception as e:
        logger.error(f"Error checking TTS availability: {e}")
        return False


def get_available_languages() -> list:
    """Get list of supported language codes."""
    return list(PIPER_VOICE_MAP.keys())


def get_voice_info(language: str) -> dict:
    """
    Get information about the voice used for a language.

    Returns:
        dict: {
            "language": str,
            "voice_name": str,
            "is_native": bool,  # True if native voice, False if fallback
        }
    """
    voice_info = PIPER_VOICE_MAP.get(language.lower(), (DEFAULT_VOICE, False))
    return {
        "language": language,
        "voice_name": voice_info[0],
        "is_native": voice_info[1],
    }


def preload_voices(languages: list = None):
    """
    Preload voice models to avoid first-request delay.
    Useful in production to warm up the cache.

    Args:
        languages: List of language codes to preload.
                   If None, preloads common languages.
    """
    if languages is None:
        # Preload most common languages for Dr-Lingo
        languages = ["en", "es", "afr", "zul", "xho"]

    logger.info(f"Preloading {len(languages)} Piper voices...")

    for lang in languages:
        try:
            get_piper_voice(lang)
            logger.info(f"✓ Preloaded {lang}")
        except Exception as e:
            logger.warning(f"✗ Failed to preload {lang}: {e}")

    logger.info("Voice preloading complete")
