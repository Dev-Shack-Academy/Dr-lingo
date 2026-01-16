from unittest.mock import MagicMock, patch

import pytest
from api.models import Collection, CollectionItem
from django.core.management import call_command


@pytest.mark.django_db
class TestManagementCommands:
    @patch("api.tasks.rag_tasks.process_document_async.apply")
    def test_reembed_everything_logic(self, mock_apply, db):
        collection = Collection.objects.create(name="Test Col")
        CollectionItem.objects.create(collection=collection, name="Item 1", content="Content 1", embedding=None)
        CollectionItem.objects.create(collection=collection, name="Item 2", content="Content 2", embedding=[0.1] * 768)

        mock_apply.return_value = MagicMock(result="success")

        # Should only process item1 by default
        call_command("reembed_everything")
        assert mock_apply.call_count == 1

        mock_apply.reset_mock()

        # Should process all items with --all
        call_command("reembed_everything", "--all")
        assert mock_apply.call_count == 2

    @patch("api.tasks.rag_tasks.process_document_async.delay")
    def test_reembed_everything_async(self, mock_delay, db):
        collection = Collection.objects.create(name="Test Col")
        item = CollectionItem.objects.create(collection=collection, name="Item 1", content="Content 1", embedding=None)

        call_command("reembed_everything", "--async")
        mock_delay.assert_called_once_with(document_id=item.id)
