from unittest.mock import MagicMock, patch

import pytest
from api.models.chat import ChatMessage, ChatRoom
from api.models.rag import Collection, CollectionItem
from api.tasks.assistance_tasks import generate_doctor_assistance_async
from api.tasks.audio_tasks import transcribe_audio_async
from api.tasks.dataset_tasks import import_all_hf_languages
from api.tasks.rag_tasks import generate_embeddings_async, process_document_async, reindex_collection
from api.tasks.translation_tasks import batch_translate, get_translation_cache_key, translate_text_async


@pytest.mark.django_db
class TestCeleryTasks:
    @patch("api.services.ai.get_translation_service")
    def test_translate_text_async(self, mock_get_translation_service, db):
        room = ChatRoom.objects.create(name="Task Room", patient_language="en", doctor_language="sw")
        message = ChatMessage.objects.create(
            room=room, sender_type="patient", original_text="Hello", original_language="en"
        )

        mock_provider = MagicMock()
        mock_provider.translate_with_context.return_value = "Jambo"
        mock_get_translation_service.return_value = mock_provider

        translate_text_async(message_id=message.id, text="Hello", source_lang="en", target_lang="sw")

        message.refresh_from_db()
        assert message.translated_text == "Jambo"
        assert message.translated_language == "sw"

    @patch("api.services.ai.get_transcription_service")
    @patch("api.tasks.translation_tasks.translate_text_async.delay")
    def test_transcribe_audio_async(self, mock_translate_delay, mock_get_transcription_service, db):
        room = ChatRoom.objects.create(name="Audio Room", patient_language="en", doctor_language="zu")
        message = ChatMessage.objects.create(room=room, sender_type="patient")

        mock_transcription_service = MagicMock()
        mock_transcription_service.transcribe.return_value = {"success": True, "transcription": "Ngiyaphila"}
        mock_get_transcription_service.return_value = mock_transcription_service

        transcribe_audio_async(message_id=message.id, audio_data=b"fake audio", source_lang="zu")

        message.refresh_from_db()
        assert message.audio_transcription == "Ngiyaphila"
        assert message.original_text == "Ngiyaphila"
        mock_translate_delay.assert_called_once()

    @patch("api.services.rag_service.RAGService._generate_embedding")
    @patch("api.services.rag_service.RAGService._setup_client")
    def test_process_document_async_no_chunking(self, mock_setup, mock_gen_embedding, db):
        col = Collection.objects.create(name="Test Col", description="Test")
        item = CollectionItem.objects.create(collection=col, name="Doc", content="Short content")

        mock_gen_embedding.return_value = [0.1] * 768

        process_document_async(item.id)

        item.refresh_from_db()
        assert item.embedding is not None
        assert len(item.embedding) == 768

    @patch("api.tasks.rag_tasks.process_document_async.delay")
    def test_generate_embeddings_async(self, mock_process_delay, db):
        col = Collection.objects.create(name="Test Col", description="Test")
        CollectionItem.objects.create(collection=col, name="Doc 1", content="Content 1")
        CollectionItem.objects.create(collection=col, name="Doc 2", content="Content 2")

        generate_embeddings_async(col.id)
        assert mock_process_delay.call_count == 2

    @patch("api.tasks.pdf_tasks.extract_pdf_text")
    @patch("api.services.rag_service.RAGService._generate_embedding")
    @patch("api.services.rag_service.RAGService._setup_client")
    @patch("os.path.exists")
    @patch("os.remove")
    def test_process_pdf_document_async(
        self, mock_remove, mock_exists, mock_setup, mock_gen_embedding, mock_extract_pdf, db
    ):
        from api.tasks.pdf_tasks import process_pdf_document_async

        col = Collection.objects.create(name="PDF Col", description="Test")

        mock_extract_pdf.return_value = "Extracted PDF text"
        mock_gen_embedding.return_value = [0.1] * 768
        mock_exists.return_value = True

        result = process_pdf_document_async(
            collection_id=col.id, file_path="/tmp/test.pdf", name="Test PDF", description="Test description"
        )

        assert result["success"] is True
        assert result["name"] == "Test PDF"
        assert CollectionItem.objects.filter(collection=col).exists()

    @patch("api.services.tts_service.text_to_speech")
    @patch("api.services.tts_service.is_tts_available")
    def test_generate_tts_async(self, mock_tts_available, mock_text_to_speech, db):
        from api.models.chat import ChatMessage, ChatRoom
        from api.tasks.tts_tasks import generate_tts_async

        room = ChatRoom.objects.create(name="TTS Room")
        message = ChatMessage.objects.create(
            room=room, sender_type="patient", original_text="Hello", translated_text="Hola", translated_language="es"
        )

        mock_tts_available.return_value = True
        mock_text_to_speech.return_value = {"success": True, "file_path": "/tmp/tts_123.wav"}

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = b"fake audio data"
            with patch("os.path.exists", return_value=True):
                with patch("os.remove"):
                    result = generate_tts_async(
                        message_id=message.id, text="Hola", language="es", speaker_type="patient"
                    )

        assert result["success"] is True
        message.refresh_from_db()
        assert message.tts_audio is not None

    @patch("api.services.rag_service.RAGService.query_and_answer")
    @patch("api.services.rag_service.RAGService._setup_client")
    def test_generate_doctor_assistance_async(self, mock_setup, mock_query_answer, db):
        """Test doctor assistance with a RAG collection configured."""
        # Create collection first
        collection = Collection.objects.create(
            name="Test Collection", description="Test", collection_type=Collection.CollectionType.PATIENT_CONTEXT
        )

        # Create room with RAG collection
        room = ChatRoom.objects.create(name="Assistance Room", rag_collection=collection)
        ChatMessage.objects.create(
            room=room, sender_type="patient", original_text="I have a headache", translated_text="Me duele la cabeza"
        )

        mock_query_answer.return_value = {
            "status": "success",
            "answer": "Based on the symptoms, consider asking about duration and severity.",
            "sources": [],
        }

        result = generate_doctor_assistance_async(room.id)

        assert result["status"] == "success"
        assert "consider asking" in result["assistance"]

    def test_generate_doctor_assistance_no_collection(self, db):
        """Test doctor assistance returns no_collection when no RAG configured."""
        room = ChatRoom.objects.create(name="No Collection Room")

        result = generate_doctor_assistance_async(room.id)

        assert result["status"] == "no_collection"

    @patch("api.tasks.dataset_tasks.import_hf_dataset_async.delay")
    def test_import_all_hf_languages(self, mock_import_delay, db):
        result = import_all_hf_languages(limit=10)

        assert result["status"] == "queued"
        assert result["count"] == 20  # All supported languages
        assert mock_import_delay.call_count == 20

    def test_get_translation_cache_key(self):
        """Test translation cache key generation."""
        key = get_translation_cache_key("Hello", "en", "es")

        assert key.startswith("translation:")
        assert len(key) == 28  # "translation:" + 16 char hash

        # Same inputs should generate same key
        key2 = get_translation_cache_key("Hello", "en", "es")
        assert key == key2

        # Different inputs should generate different keys
        key3 = get_translation_cache_key("Hello", "en", "fr")
        assert key != key3

    @patch("django.core.cache.cache.get")
    def test_batch_translate_with_cache(self, mock_cache_get, db):
        """Test batch translation with cached results."""
        translations = [
            {"text": "Hello", "source_lang": "en", "target_lang": "es"},
            {"text": "World", "source_lang": "en", "target_lang": "es"},
        ]

        # Mock cache hits
        mock_cache_get.side_effect = ["Hola", None]  # First cached, second not

        results = batch_translate(translations)

        assert len(results) == 2
        assert results[0]["translation"] == "Hola"
        assert results[0]["cached"] is True
        assert results[1]["status"] == "queued"

    @patch("api.tasks.rag_tasks.generate_embeddings_async.delay")
    def test_reindex_collection_task(self, mock_gen_embeddings, db):
        """Test collection reindexing task."""
        collection = Collection.objects.create(name="Test Collection", description="Test")
        CollectionItem.objects.create(collection=collection, name="Item 1", content="Content", embedding=[0.1] * 768)

        result = reindex_collection(collection.id)

        assert result["status"] == "success"
        assert result["message"] == "Reindex started"
        mock_gen_embeddings.assert_called_once_with(collection.id)

        # Verify embeddings were cleared
        item = CollectionItem.objects.get(collection=collection)
        assert item.embedding is None

    def test_cleanup_old_audio_files(self, db):
        """Test cleanup of old audio files."""
        from api.tasks.cleanup_tasks import cleanup_old_audio_files

        # Just test that it runs without error (no old files to clean)
        result = cleanup_old_audio_files(days_old=30)

        assert result["status"] == "success"
        assert "deleted" in result

    def test_cleanup_expired_cache(self, db):
        """Test cache cleanup task."""
        from api.tasks.cleanup_tasks import cleanup_expired_cache

        result = cleanup_expired_cache()

        assert result["status"] == "success"

    def test_database_maintenance(self, db):
        """Test database maintenance task."""
        from api.tasks.cleanup_tasks import database_maintenance

        result = database_maintenance()

        assert result["status"] == "success"

    def test_generate_usage_report(self, db):
        """Test usage report generation."""
        from api.tasks.cleanup_tasks import generate_usage_report

        # Create some test data
        room = ChatRoom.objects.create(name="Test Room")
        ChatMessage.objects.create(room=room, sender_type="patient", original_text="Test")

        result = generate_usage_report()

        # The function returns a report dict, not a status dict
        assert "date" in result
        assert "messages_by_day" in result
        assert "active_rooms_today" in result
