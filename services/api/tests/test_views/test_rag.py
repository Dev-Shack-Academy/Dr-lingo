from unittest.mock import MagicMock, patch

import pytest
from api.models.rag import Collection, CollectionItem
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestRAGViews:
    def test_list_collections(self, admin_client, db):
        Collection.objects.create(name="Global KB", collection_type="knowledge_base")
        url = reverse("collection-list")
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_create_collection_admin(self, admin_client):
        url = reverse("collection-list")
        data = {"name": "New KB", "description": "New Knowledge Base", "collection_type": "knowledge_base"}
        response = admin_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Collection.objects.filter(name="New KB").exists()

    def test_create_collection_denied_for_doctor(self, auth_client):
        url = reverse("collection-list")
        data = {"name": "Hacker KB", "collection_type": "knowledge_base"}
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch("api.services.rag.v2.RAGServiceV2.query_and_answer")
    def test_query_collection(self, mock_query, admin_client, db):
        collection = Collection.objects.create(name="Query KB")
        mock_query.return_value = {"status": "success", "answer": "Mocked Answer", "sources": []}

        url = reverse("collection-query-and-answer", args=[collection.id])
        response = admin_client.post(url, {"query": "What is COVID-19?"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["answer"] == "Mocked Answer"

    @patch("api.tasks.rag_tasks.process_document_async.delay")
    def test_add_document_async(self, mock_delay, admin_client, db):
        collection = Collection.objects.create(name="Target Col")
        url = reverse("collection-add-document", args=[collection.id])
        data = {"name": "Doc 1", "content": "This is a document", "async": "true"}
        response = admin_client.post(url, data)
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert CollectionItem.objects.filter(name="Doc 1").exists()
        mock_delay.assert_called_once()

    @patch("api.views.rag.CELERY_ENABLED", True)
    @patch("api.tasks.rag_tasks.reindex_collection.delay")
    def test_reindex_collection(self, mock_reindex, admin_client, db):
        """Test reindexing collection triggers Celery task."""
        collection = Collection.objects.create(name="Reindex Col")
        mock_reindex.return_value = MagicMock(id="test-task-id")

        url = reverse("collection-reindex", args=[collection.id])
        response = admin_client.post(url)

        assert response.status_code == status.HTTP_202_ACCEPTED
        mock_reindex.assert_called_once_with(collection_id=collection.id)
