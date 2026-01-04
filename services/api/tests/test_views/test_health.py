from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestHealthViews:
    def test_health_check_public_access(self, api_client):
        """Test health check endpoint is publicly accessible."""
        url = reverse("health-check")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ok"
        assert response.data["message"] == "pong"

    def test_ai_config_requires_authentication(self, api_client):
        """Test AI config endpoint requires authentication."""
        url = reverse("ai-config")
        response = api_client.get(url)

        # Returns 403 for unauthenticated users (IsAuthenticated permission)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_ai_config_ollama_provider(self, auth_client, settings):
        """Test AI config endpoint with Ollama provider."""
        settings.AI_PROVIDER = "ollama"
        settings.OLLAMA_TRANSLATION_MODEL = "test-translation-model"
        settings.OLLAMA_COMPLETION_MODEL = "test-completion-model"
        settings.OLLAMA_EMBEDDING_MODEL = "test-embedding-model"
        settings.OLLAMA_BASE_URL = "http://localhost:11434"

        url = reverse("ai-config")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["ai_provider"] == "ollama"
        assert data["translation_model"] == "test-translation-model"
        assert data["completion_model"] == "test-completion-model"
        assert data["embedding_model"] == "test-embedding-model"
        assert data["embedding_provider"] == "ollama"
        assert data["ollama_base_url"] == "http://localhost:11434"
        assert data["embedding_dimensions"] == 768
        assert data["chunking_strategy"] == "fixed-length"

    def test_ai_config_gemini_provider(self, auth_client, settings):
        """Test AI config endpoint with Gemini provider."""
        settings.AI_PROVIDER = "gemini"
        settings.GEMINI_MODEL = "gemini-1.5-flash"
        settings.GEMINI_EMBEDDING_MODEL = "text-embedding-004"

        url = reverse("ai-config")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["ai_provider"] == "gemini"
        assert data["translation_model"] == "gemini-1.5-flash"
        assert data["completion_model"] == "gemini-1.5-flash"
        assert data["embedding_model"] == "text-embedding-004"
        assert data["embedding_provider"] == "gemini"

    def test_task_status_requires_admin(self, auth_client):
        """Test task status endpoint requires admin permissions."""
        url = reverse("task-status", args=["test-task-id"])
        response = auth_client.get(url)

        # Doctor user should get 403 (IsAdmin permission)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_task_status_success(self, admin_client, settings):
        """Test task status endpoint with successful task."""
        settings.CELERY_BROKER_URL = "redis://localhost:6379/0"

        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.result = {"status": "completed"}

        with patch("celery.result.AsyncResult", return_value=mock_result):
            url = reverse("task-status", args=["test-task-id"])
            response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "SUCCESS"
        assert data["ready"] is True
        assert data["result"] == {"status": "completed"}

    def test_task_status_failed(self, admin_client, settings):
        """Test task status endpoint with failed task."""
        settings.CELERY_BROKER_URL = "redis://localhost:6379/0"

        mock_result = MagicMock()
        mock_result.status = "FAILURE"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = False
        mock_result.result = Exception("Task failed")

        with patch("celery.result.AsyncResult", return_value=mock_result):
            url = reverse("task-status", args=["test-task-id"])
            response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["status"] == "FAILURE"
        assert data["ready"] is True
        assert "error" in data

    def test_task_status_celery_not_configured(self, admin_client, settings):
        """Test task status when Celery is not configured."""
        settings.CELERY_BROKER_URL = None

        url = reverse("task-status", args=["test-task-id"])
        response = admin_client.get(url)

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Celery is not configured" in response.data["error"]

    def test_celery_status_requires_admin(self, auth_client):
        """Test Celery status endpoint requires admin permissions."""
        url = reverse("celery-status")
        response = auth_client.get(url)

        # Doctor user should get 403 (IsAdmin permission)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_celery_status_not_configured(self, admin_client, settings):
        """Test Celery status when not configured."""
        settings.CELERY_BROKER_URL = None

        url = reverse("celery-status")
        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["celery_enabled"] is False
        assert "not configured" in data["message"]

    def test_celery_status_with_workers(self, admin_client, settings):
        """Test Celery status with active workers."""
        settings.CELERY_BROKER_URL = "redis://localhost:6379/0"

        mock_inspect = MagicMock()
        mock_inspect.active.return_value = {"worker1@hostname": [], "worker2@hostname": []}
        mock_app = MagicMock()
        mock_app.control.inspect.return_value = mock_inspect

        with patch("config.celery.app", mock_app):
            url = reverse("celery-status")
            response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["celery_enabled"] is True
        assert data["workers_available"] is True
        assert data["worker_count"] == 2
        assert len(data["worker_names"]) == 2

    def test_celery_status_no_workers(self, admin_client, settings):
        """Test Celery status with no active workers."""
        settings.CELERY_BROKER_URL = "redis://localhost:6379/0"

        mock_inspect = MagicMock()
        mock_inspect.active.return_value = None
        mock_app = MagicMock()
        mock_app.control.inspect.return_value = mock_inspect

        with patch("config.celery.app", mock_app):
            url = reverse("celery-status")
            response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["celery_enabled"] is True
        assert data["workers_available"] is False
        assert data["worker_count"] == 0

    def test_celery_status_exception(self, admin_client, settings):
        """Test Celery status when inspection fails."""
        settings.CELERY_BROKER_URL = "redis://localhost:6379/0"

        mock_app = MagicMock()
        mock_app.control.inspect.side_effect = Exception("Connection failed")

        with patch("config.celery.app", mock_app):
            url = reverse("celery-status")
            response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["celery_enabled"] is True
        assert data["workers_available"] is False
        assert "Connection failed" in data["error"]
