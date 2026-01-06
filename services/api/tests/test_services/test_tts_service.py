"""
Tests for Piper TTS service.

Updated for Piper TTS migration (January 2026).
"""

from unittest.mock import MagicMock, patch

from api.services.tts_service import (
    get_available_languages,
    get_voice_info,
    is_tts_available,
)


class TestTTSService:
    def test_voice_info_native_language(self):
        """Test voice info for natively supported languages."""
        info = get_voice_info("en")
        assert info["language"] == "en"
        assert info["voice_name"] == "en_US-lessac-medium"
        assert info["is_native"] is True

        info = get_voice_info("afr")
        assert info["language"] == "afr"
        assert info["voice_name"] == "af_ZA-google-medium"
        assert info["is_native"] is True  # Afrikaans has native Piper support!

    def test_voice_info_fallback_language(self):
        """Test voice info for languages that fall back to English."""
        info = get_voice_info("zul")
        assert info["language"] == "zul"
        assert info["voice_name"] == "en_US-lessac-medium"
        assert info["is_native"] is False

        info = get_voice_info("xho")
        assert info["is_native"] is False

    def test_voice_info_unknown_language(self):
        """Test voice info for unknown language defaults to English."""
        info = get_voice_info("unknown")
        assert info["voice_name"] == "en_US-lessac-medium"
        assert info["is_native"] is False

    def test_get_available_languages(self):
        """Test that available languages list is populated."""
        languages = get_available_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "en" in languages
        assert "es" in languages
        assert "afr" in languages
        assert "zul" in languages

    @patch("importlib.util.find_spec")
    def test_is_tts_available_true(self, mock_find_spec):
        """Test TTS availability check when Piper is installed."""
        mock_find_spec.return_value = MagicMock()
        assert is_tts_available() is True
        mock_find_spec.assert_called_with("piper")

    @patch("importlib.util.find_spec")
    def test_is_tts_available_false(self, mock_find_spec):
        """Test TTS availability check when Piper is not installed."""
        mock_find_spec.return_value = None
        assert is_tts_available() is False

    @patch("api.services.tts_service.get_piper_voice")
    def test_text_to_speech_empty_text(self, mock_get_voice):
        """Test text_to_speech with empty text."""
        from api.services.tts_service import text_to_speech

        result = text_to_speech("", "en", output_path="/tmp/test.wav")

        assert result["success"] is False
        assert "Empty text" in result["error"]
        mock_get_voice.assert_not_called()

    @patch("api.services.tts_service.get_piper_voice")
    def test_text_to_speech_whitespace_only(self, mock_get_voice):
        """Test text_to_speech with whitespace-only text."""
        from api.services.tts_service import text_to_speech

        result = text_to_speech("   ", "en", output_path="/tmp/test.wav")

        assert result["success"] is False
        assert "Empty text" in result["error"]

    @patch("os.path.getsize")
    @patch("wave.open")
    @patch("os.makedirs")
    @patch("api.services.tts_service.get_piper_voice")
    def test_text_to_speech_success(self, mock_get_voice, mock_makedirs, mock_wave_open, mock_getsize):
        """Test successful text-to-speech generation."""
        from api.services.tts_service import text_to_speech

        mock_voice = MagicMock()
        mock_get_voice.return_value = mock_voice
        mock_getsize.return_value = 12345

        result = text_to_speech(text="Hello world", language="en", output_path="/tmp/test.wav")

        assert result["success"] is True
        assert result["file_path"] == "/tmp/test.wav"
        assert result["file_size"] == 12345
        mock_voice.synthesize.assert_called_once()

    @patch("os.path.getsize")
    @patch("wave.open")
    @patch("os.makedirs")
    @patch("api.services.tts_service.get_piper_voice")
    def test_text_to_speech_with_speed(self, mock_get_voice, mock_makedirs, mock_wave_open, mock_getsize):
        """Test text-to-speech with custom speed."""
        from api.services.tts_service import text_to_speech

        mock_voice = MagicMock()
        mock_get_voice.return_value = mock_voice
        mock_getsize.return_value = 12345

        result = text_to_speech(text="Hello", language="en", output_path="/tmp/test.wav", speed=0.8)

        assert result["success"] is True
        call_kwargs = mock_voice.synthesize.call_args.kwargs
        assert call_kwargs["length_scale"] == 0.8

    @patch("api.services.tts_service.get_piper_voice")
    def test_text_to_speech_exception(self, mock_get_voice):
        """Test text-to-speech when Piper raises exception."""
        from api.services.tts_service import text_to_speech

        mock_get_voice.side_effect = Exception("Piper model error")

        result = text_to_speech("Hello", "en", output_path="/tmp/test.wav")

        assert result["success"] is False
        assert "Piper model error" in result["error"]

    def test_piper_voice_caching(self):
        """Test that Piper voices are cached after first load."""
        import api.services.tts_service as tts_module

        # The module should have a _piper_voices dict for caching
        assert hasattr(tts_module, "_piper_voices")
        assert isinstance(tts_module._piper_voices, dict)

    def test_voice_map_structure(self):
        """Test that voice map has correct structure."""
        from api.services.tts_service import PIPER_VOICE_MAP

        assert isinstance(PIPER_VOICE_MAP, dict)

        # Check structure: each value should be (voice_name, is_native)
        for lang, info in PIPER_VOICE_MAP.items():
            assert isinstance(info, tuple)
            assert len(info) == 2
            assert isinstance(info[0], str)  # voice_name
            assert isinstance(info[1], bool)  # is_native

    def test_afrikaans_native_support(self):
        """Test that Afrikaans has native Piper support (not English fallback)."""
        from api.services.tts_service import PIPER_VOICE_MAP

        afr_info = PIPER_VOICE_MAP.get("afr")
        assert afr_info is not None
        assert afr_info[1] is True  # is_native should be True
        assert "af_ZA" in afr_info[0]  # Should use Afrikaans voice

    def test_sa_languages_fallback(self):
        """Test that other SA languages fall back to English."""
        from api.services.tts_service import PIPER_VOICE_MAP

        sa_fallback_langs = ["zul", "xho", "sot", "nso", "tsn", "ssw", "ven", "tso", "nbl"]

        for lang in sa_fallback_langs:
            info = PIPER_VOICE_MAP.get(lang)
            assert info is not None, f"Missing language: {lang}"
            assert info[1] is False, f"{lang} should have is_native=False"
            assert "en_US" in info[0], f"{lang} should use English voice"

    @patch("api.services.tts_service.get_piper_voice")
    @patch("api.services.tts_service.logger")
    def test_preload_voices(self, mock_logger, mock_get_voice):
        """Test voice preloading function."""
        from api.services.tts_service import preload_voices

        mock_get_voice.return_value = MagicMock()

        preload_voices(["en", "es"])

        assert mock_get_voice.call_count == 2

    @patch("api.services.tts_service.get_piper_voice")
    def test_preload_voices_with_error(self, mock_get_voice):
        """Test voice preloading handles errors gracefully."""
        from api.services.tts_service import preload_voices

        mock_get_voice.side_effect = Exception("Model not found")

        # Should not raise, just log warning
        preload_voices(["en"])

    def test_speaker_params_ignored(self):
        """Test that speaker_wav and speaker_type params are accepted but ignored."""
        from api.services.tts_service import text_to_speech

        # These params should be accepted for API compatibility
        # but Piper doesn't use them (no voice cloning)
        with patch("api.services.tts_service.get_piper_voice") as mock_get_voice:
            mock_get_voice.side_effect = Exception("Test")

            # Should not raise TypeError for extra params
            result = text_to_speech(
                text="Hello",
                language="en",
                speaker_wav="/path/to/speaker.wav",
                speaker_type="doctor",
                output_path="/tmp/test.wav",
            )

            assert result["success"] is False
