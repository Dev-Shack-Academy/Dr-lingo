from unittest.mock import MagicMock, patch

from api.services.ai.factory import AIProviderFactory
from api.services.ai.gemini_provider import GeminiTranslationService
from api.services.ai.ollama_provider import OllamaTranslationService


class TestAIServices:
    @patch("api.services.ai.ollama_provider.requests.post")
    def test_ollama_provider_translate(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Holla"}
        mock_post.return_value = mock_response

        # We need to mock get_language_name because it's used in translate
        with patch("api.services.ai.ollama_provider.get_language_name", side_effect=lambda x: x):
            provider = OllamaTranslationService()
            result = provider.translate("Hello", "en", "sw")
            assert result == "Holla"
            mock_post.assert_called_once()

    @patch("api.services.ai.gemini_provider.genai.GenerativeModel")
    @patch("api.services.ai.gemini_provider.genai.configure")
    def test_gemini_provider_translate(self, mock_config, mock_model_class, settings):
        settings.GEMINI_API_KEY = "test-key"
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Generated text"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        provider = GeminiTranslationService()
        result = provider.translate("Hello", "en", "sw")
        assert result == "Generated text"

    def test_factory_get_provider(self, settings):
        import traceback

        try:
            settings.GEMINI_API_KEY = "test-key"
            settings.AI_PROVIDER = "ollama"
            factory = AIProviderFactory()
            provider = factory.get_translation_service()
            assert isinstance(provider, OllamaTranslationService)

            settings.AI_PROVIDER = "gemini"
            factory = AIProviderFactory()
            provider = factory.get_translation_service()
            assert isinstance(provider, GeminiTranslationService)
        except Exception:
            traceback.print_exc()
            raise
