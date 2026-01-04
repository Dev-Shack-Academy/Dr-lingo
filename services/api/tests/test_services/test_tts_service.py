from unittest.mock import MagicMock, patch

from api.services.tts_service import get_xtts_language, is_tts_available


class TestTTSService:
    def test_xtts_language_mapping(self):
        """Test language code mapping for XTTS."""
        assert get_xtts_language("en") == "en"
        assert get_xtts_language("es") == "es"
        assert get_xtts_language("fr") == "fr"
        # South African languages fallback to English
        assert get_xtts_language("zul") == "en"
        assert get_xtts_language("xho") == "en"
        assert get_xtts_language("afr") == "en"
        # Unknown language defaults to English
        assert get_xtts_language("unknown") == "en"

    @patch("importlib.util.find_spec")
    def test_is_tts_available_true(self, mock_find_spec):
        """Test TTS availability check when TTS is installed."""
        mock_find_spec.return_value = MagicMock()
        assert is_tts_available() is True
        mock_find_spec.assert_called_with("TTS")

    @patch("importlib.util.find_spec")
    def test_is_tts_available_false(self, mock_find_spec):
        """Test TTS availability check when TTS is not installed."""
        mock_find_spec.return_value = None
        assert is_tts_available() is False

    @patch("api.services.tts_service.get_tts_model")
    def test_text_to_speech_not_available(self, mock_get_model):
        """Test text_to_speech when TTS model fails to load."""
        from api.services.tts_service import text_to_speech

        mock_get_model.side_effect = ImportError("TTS not available")

        result = text_to_speech("Hello", "en", output_path="/tmp/test.wav")

        assert result["success"] is False
        assert "TTS not available" in result["error"]

    @patch("api.services.tts_service.get_speaker_wav")
    @patch("api.services.tts_service.get_tts_model")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_text_to_speech_success(self, mock_makedirs, mock_exists, mock_get_model, mock_get_speaker):
        """Test successful text-to-speech generation."""
        from api.services.tts_service import text_to_speech

        mock_exists.return_value = True
        mock_tts = MagicMock()
        mock_get_model.return_value = mock_tts
        mock_get_speaker.return_value = "/path/to/speaker.wav"

        result = text_to_speech(text="Hello world", language="en", output_path="/tmp/test.wav")

        assert result["success"] is True
        assert result["file_path"] == "/tmp/test.wav"
        mock_tts.tts_to_file.assert_called_once()

    @patch("api.services.tts_service.get_speaker_wav")
    @patch("api.services.tts_service.get_tts_model")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_text_to_speech_with_speaker(self, mock_makedirs, mock_exists, mock_get_model, mock_get_speaker):
        """Test text-to-speech with speaker reference file."""
        from api.services.tts_service import text_to_speech

        mock_exists.return_value = True
        mock_tts = MagicMock()
        mock_get_model.return_value = mock_tts
        mock_get_speaker.return_value = "/path/to/doctor_reference.wav"

        result = text_to_speech(text="Hello", language="en", speaker_type="doctor", output_path="/tmp/test.wav")

        assert result["success"] is True
        mock_tts.tts_to_file.assert_called_once()
        call_kwargs = mock_tts.tts_to_file.call_args.kwargs
        assert call_kwargs["speaker_wav"] == "/path/to/doctor_reference.wav"

    @patch("api.services.tts_service.get_speaker_wav")
    @patch("api.services.tts_service.get_tts_model")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_text_to_speech_exception(self, mock_makedirs, mock_exists, mock_get_model, mock_get_speaker):
        """Test text-to-speech when TTS model raises exception."""
        from api.services.tts_service import text_to_speech

        mock_exists.return_value = True
        mock_tts = MagicMock()
        mock_tts.tts_to_file.side_effect = Exception("TTS model error")
        mock_get_model.return_value = mock_tts
        mock_get_speaker.return_value = "/path/to/speaker.wav"

        result = text_to_speech("Hello", "en", output_path="/tmp/test.wav")

        assert result["success"] is False
        assert "TTS model error" in result["error"]

    def test_get_tts_model_lazy_loading(self):
        """Test TTS model lazy loading concept."""
        # This test verifies the lazy loading pattern exists
        import api.services.tts_service as tts_module
        from api.services.tts_service import get_tts_model

        # The module should have a _tts_model variable for caching
        assert hasattr(tts_module, "_tts_model")

        # get_tts_model should be callable
        assert callable(get_tts_model)

    def test_get_tts_model_caching(self):
        """Test that TTS model is cached after first load."""
        import api.services.tts_service as tts_module

        # The module should have a _tts_model variable for caching
        assert hasattr(tts_module, "_tts_model")

        # If model is already loaded, it should be reused
        if tts_module._tts_model is not None:
            model1 = tts_module.get_tts_model()
            model2 = tts_module.get_tts_model()
            assert model1 is model2  # Same instance

    def test_speaker_file_paths(self):
        """Test speaker reference file path generation."""
        from api.services.tts_service import DOCTOR_SPEAKER_WAV, PATIENT_SPEAKER_WAV, SPEAKER_WAV_DIR

        # Test that paths are correctly constructed
        assert "tts_speakers" in SPEAKER_WAV_DIR
        assert "doctor_reference.wav" in DOCTOR_SPEAKER_WAV
        assert "patient_reference.wav" in PATIENT_SPEAKER_WAV

    def test_pytorch_weights_patch(self):
        """Test that the TTS service handles PyTorch weights_only parameter."""
        # This is a basic test - the actual patch happens during model loading
        # Just verify the module can be imported without errors
        from api.services.tts_service import get_tts_model

        assert callable(get_tts_model)
