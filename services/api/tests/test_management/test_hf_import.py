from unittest.mock import MagicMock, patch

import pytest
from api.models import Collection
from django.core.management import call_command


@pytest.mark.django_db
class TestHFImportCommand:
    @patch("api.management.commands.import_hf_dataset.Command._import_dataset")
    @patch("importlib.util.find_spec", return_value=True)
    def test_import_hf_dataset(self, mock_find_spec, mock_import_dataset, db):
        # Mock requests inside handle
        with patch("requests.get") as mock_requests_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": [{"name": "nomic-embed-text:v1.5"}]}
            mock_requests_get.return_value = mock_response

            # Run command
            call_command("import_hf_dataset", "--lang", "zul", "--limit", "1")

            # Check if collection was created
            assert Collection.objects.filter(name__contains="isiZulu").exists()
            mock_import_dataset.assert_called_once()

    @patch("api.services.rag_service.RAGService.add_document")
    @patch("datasets.load_dataset")
    def test_import_dataset_logic(self, mock_load_dataset, mock_add_doc, db):
        from api.management.commands.import_hf_dataset import Command

        cmd = Command()

        mock_item = {"transcription": "Test transcript", "speaker_id": "spk1"}
        mock_load_dataset.return_value = [mock_item]

        collection = Collection.objects.create(name="Test Col")
        # We need to mock Audio cast column calls if any
        mock_ds = MagicMock()
        mock_ds.__iter__.return_value = [mock_item]
        mock_load_dataset.return_value = mock_ds

        cmd._import_dataset(collection, "zul", "train", False, 1, False)
        mock_add_doc.assert_called_once()
