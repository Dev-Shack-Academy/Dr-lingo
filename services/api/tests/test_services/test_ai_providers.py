"""
Tests for AI Provider Services and Prompt Management.

Tests cover:
- Prompt module (base classes, versioning, rendering)
- Translation prompts (V1, V2)
- Completion and transcription prompts (simple, no versioning)
- Provider implementations (Ollama, Gemini)
- Factory pattern
"""

from unittest.mock import MagicMock, patch

from api.services.ai.factory import AIProviderFactory
from api.services.ai.gemini_provider import GeminiTranslationService
from api.services.ai.ollama_provider import OllamaTranslationService
from api.services.ai.prompts import (
    CompletionPrompt,
    CompletionWithContextPrompt,
    PromptVersion,
    TranscriptionPrompt,
    TranslationPromptV1,
    TranslationPromptV2,
    get_completion_prompt,
    get_completion_with_context_prompt,
    # Transcription (simple)
    get_transcription_prompt,
    # Translation (versioned)
    get_translation_prompt,
    get_translation_with_context_prompt,
)
from api.services.ai.prompts.base import PromptMetadata

# =============================================================================
# Prompt Base Tests
# =============================================================================


class TestPromptBase:
    """Tests for base prompt classes."""

    def test_prompt_version_enum(self):
        """Test PromptVersion enum values."""
        assert PromptVersion.V1.value == "v1"
        assert PromptVersion.V2.value == "v2"
        assert PromptVersion.LATEST.value == "latest"

    def test_prompt_metadata(self):
        """Test PromptMetadata dataclass."""
        metadata = PromptMetadata(
            version=PromptVersion.V1,
            name="test_prompt",
            description="A test prompt",
            author="test",
            tags=["test", "example"],
        )
        assert metadata.version == PromptVersion.V1
        assert metadata.name == "test_prompt"
        assert metadata.tags == ["test", "example"]


# =============================================================================
# Translation Prompt Tests (Versioned)
# =============================================================================


class TestTranslationPrompts:
    """Tests for versioned translation prompts."""

    def test_get_translation_prompt_v1(self):
        """Test getting V1 translation prompt."""
        prompt = get_translation_prompt(PromptVersion.V1)
        assert prompt.version == PromptVersion.V1
        assert prompt.name == "translation_basic"
        assert isinstance(prompt, TranslationPromptV1)

    def test_get_translation_prompt_v2(self):
        """Test getting V2 translation prompt."""
        prompt = get_translation_prompt(PromptVersion.V2)
        assert prompt.version == PromptVersion.V2
        assert prompt.name == "translation_basic_v2"
        assert isinstance(prompt, TranslationPromptV2)

    def test_get_translation_prompt_latest_is_v2(self):
        """Test LATEST points to V2."""
        prompt = get_translation_prompt(PromptVersion.LATEST)
        assert isinstance(prompt, TranslationPromptV2)

    def test_translation_v1_render(self):
        """Test V1 translation prompt rendering."""
        prompt = get_translation_prompt(PromptVersion.V1)
        rendered = prompt.render(
            text="Hello",
            source_lang="English",
            target_lang="Zulu",
        )
        assert "Hello" in rendered
        assert "English" in rendered
        assert "Zulu" in rendered
        assert "translator" in rendered.lower()

    def test_translation_v2_render(self):
        """Test V2 translation prompt rendering."""
        prompt = get_translation_prompt(PromptVersion.V2)
        rendered = prompt.render(
            text="Hello",
            source_lang="English",
            target_lang="Zulu",
        )
        assert "Hello" in rendered
        assert "Zulu" in rendered
        assert "<|system|>" in rendered  # V2 uses chat format
        assert "medical" in rendered.lower()

    def test_translation_with_context_v1_render(self):
        """Test V1 context-aware translation prompt."""
        prompt = get_translation_with_context_prompt(PromptVersion.V1)
        rendered = prompt.render(
            text="How are you?",
            source_lang="English",
            target_lang="Zulu",
            conversation_history=[
                {"sender_type": "doctor", "text": "Hello"},
            ],
            sender_type="patient",
            rag_context="Medical guide for Zulu.",
        )
        assert "How are you?" in rendered
        assert "Zulu" in rendered
        assert "Medical guide" in rendered

    def test_translation_with_context_v2_render(self):
        """Test V2 context-aware translation prompt."""
        prompt = get_translation_with_context_prompt(PromptVersion.V2)
        rendered = prompt.render(
            text="How are you?",
            source_lang="English",
            target_lang="Zulu",
            conversation_history=[
                {"sender_type": "doctor", "text": "Hello"},
            ],
            sender_type="patient",
            rag_context="Medical guide for Zulu.",
        )
        assert "How are you?" in rendered
        assert "<reference_materials>" in rendered  # V2 uses XML tags
        assert "<conversation_history>" in rendered
        assert "BANTU" in rendered or "Bantu" in rendered  # V2 mentions Bantu languages
        assert "noun class" in rendered.lower()  # V2 has noun class rules

    def test_translation_v1_v2_different(self):
        """Test V1 and V2 produce different outputs."""
        v1 = get_translation_prompt(PromptVersion.V1)
        v2 = get_translation_prompt(PromptVersion.V2)

        r1 = v1.render(text="Hello", source_lang="English", target_lang="Zulu")
        r2 = v2.render(text="Hello", source_lang="English", target_lang="Zulu")

        assert r1 != r2

    def test_translation_prompt_str_repr(self):
        """Test string representations."""
        prompt = get_translation_prompt(PromptVersion.V1)
        assert "translation_basic" in str(prompt)
        assert "TranslationPromptV1" in repr(prompt)


# =============================================================================
# Completion Prompt Tests (Simple, no versioning)
# =============================================================================


class TestCompletionPrompts:
    """Tests for completion prompts (no versioning)."""

    def test_completion_prompt_passthrough(self):
        """Test basic completion is passthrough."""
        prompt = get_completion_prompt()
        rendered = prompt.render(prompt="What is diabetes?")
        assert rendered == "What is diabetes?"
        assert isinstance(prompt, CompletionPrompt)

    def test_completion_with_context(self):
        """Test completion with RAG context."""
        prompt = get_completion_with_context_prompt()
        rendered = prompt.render(
            prompt="What are the symptoms?",
            context="Diabetes causes increased thirst and frequent urination.",
        )
        assert "What are the symptoms?" in rendered
        assert "Diabetes" in rendered
        assert "<context>" in rendered
        assert isinstance(prompt, CompletionWithContextPrompt)


# =============================================================================
# Transcription Prompt Tests (Simple, no versioning)
# =============================================================================


class TestTranscriptionPrompts:
    """Tests for transcription prompt (no versioning)."""

    def test_transcription_prompt_auto_lang(self):
        """Test transcription with auto language detection."""
        prompt = get_transcription_prompt()
        rendered = prompt.render(source_lang="auto")
        assert "Detect the language" in rendered
        assert "EMPTY_AUDIO" in rendered
        assert isinstance(prompt, TranscriptionPrompt)

    def test_transcription_prompt_specific_lang(self):
        """Test transcription with specific language."""
        prompt = get_transcription_prompt()
        rendered = prompt.render(source_lang="zu")
        assert "Expected language: zu" in rendered


# =============================================================================
# Provider Tests
# =============================================================================


class TestOllamaProvider:
    """Tests for Ollama provider."""

    @patch("api.services.ai.ollama_provider.requests.post")
    def test_ollama_translate(self, mock_post):
        """Test Ollama translation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Sawubona"}
        mock_post.return_value = mock_response

        with patch("api.services.ai.ollama_provider.get_language_name", side_effect=lambda x: x):
            provider = OllamaTranslationService()
            result = provider.translate("Hello", "en", "zu")
            assert result == "Sawubona"

    @patch("api.services.ai.ollama_provider.requests.post")
    def test_ollama_translate_with_context(self, mock_post):
        """Test Ollama translation with context."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Sawubona"}
        mock_post.return_value = mock_response

        with patch("api.services.ai.ollama_provider.get_language_name", side_effect=lambda x: x):
            provider = OllamaTranslationService()
            result = provider.translate_with_context(
                text="Hello",
                source_lang="en",
                target_lang="zu",
                conversation_history=[{"sender_type": "doctor", "text": "Hi"}],
                sender_type="patient",
                rag_context="Zulu context",
            )
            assert result == "Sawubona"

    @patch("api.services.ai.ollama_provider.requests.post")
    def test_ollama_with_prompt_version(self, mock_post):
        """Test Ollama with specific prompt version."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Test"}
        mock_post.return_value = mock_response

        with patch("api.services.ai.ollama_provider.get_language_name", side_effect=lambda x: x):
            provider = OllamaTranslationService(prompt_version=PromptVersion.V1)
            assert provider.prompt_version == PromptVersion.V1


class TestGeminiProvider:
    """Tests for Gemini provider."""

    @patch("api.services.ai.gemini_provider.genai.GenerativeModel")
    @patch("api.services.ai.gemini_provider.genai.configure")
    def test_gemini_translate(self, mock_config, mock_model_class, settings):
        """Test Gemini translation."""
        settings.GEMINI_API_KEY = "test-key"
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Sawubona"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        provider = GeminiTranslationService()
        result = provider.translate("Hello", "en", "zu")
        assert result == "Sawubona"

    @patch("api.services.ai.gemini_provider.genai.GenerativeModel")
    @patch("api.services.ai.gemini_provider.genai.configure")
    def test_gemini_translate_with_context(self, mock_config, mock_model_class, settings):
        """Test Gemini translation with context."""
        settings.GEMINI_API_KEY = "test-key"
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Sawubona"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        provider = GeminiTranslationService()
        result = provider.translate_with_context(
            text="Hello",
            source_lang="en",
            target_lang="zu",
            sender_type="patient",
        )
        assert result == "Sawubona"


# =============================================================================
# Factory Tests
# =============================================================================


class TestAIProviderFactory:
    """Tests for AI provider factory."""

    def test_factory_ollama_provider(self, settings):
        """Test factory returns Ollama provider."""
        settings.AI_PROVIDER = "ollama"
        factory = AIProviderFactory()
        provider = factory.get_translation_service()
        assert isinstance(provider, OllamaTranslationService)

    @patch("api.services.ai.gemini_provider.genai.configure")
    @patch("api.services.ai.gemini_provider.genai.GenerativeModel")
    def test_factory_gemini_provider(self, mock_model, mock_config, settings):
        """Test factory returns Gemini provider."""
        settings.GEMINI_API_KEY = "test-key"
        settings.AI_PROVIDER = "gemini"
        factory = AIProviderFactory()
        provider = factory.get_translation_service()
        assert isinstance(provider, GeminiTranslationService)

    def test_factory_caches_instances(self, settings):
        """Test factory caches service instances."""
        settings.AI_PROVIDER = "ollama"
        factory = AIProviderFactory()
        provider1 = factory.get_translation_service()
        provider2 = factory.get_translation_service()
        assert provider1 is provider2

    def test_factory_different_models_different_instances(self, settings):
        """Test factory creates different instances for different models."""
        settings.AI_PROVIDER = "ollama"
        factory = AIProviderFactory()
        provider1 = factory.get_translation_service(model_name="model1")
        provider2 = factory.get_translation_service(model_name="model2")
        assert provider1 is not provider2
