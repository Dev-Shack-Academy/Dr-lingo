from unittest.mock import MagicMock

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """Fixture for DRF API client."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Fixture for an admin user."""
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="password123", role="admin"
    )


@pytest.fixture
def doctor_user(db):
    """Fixture for a doctor user."""
    return User.objects.create_user(
        username="doctor",
        email="doctor@example.com",
        password="password123",
        role="doctor",
        first_name="Doctor",
        last_name="Who",
    )


@pytest.fixture
def patient_user(db):
    """Fixture for a patient user."""
    return User.objects.create_user(
        username="patient",
        email="patient@example.com",
        password="password123",
        role="patient",
        first_name="John",
        last_name="Doe",
    )


@pytest.fixture
def auth_client(doctor_user):
    """Fixture for an authenticated API client (doctor)."""
    client = APIClient()
    client.force_authenticate(user=doctor_user)
    return client


@pytest.fixture
def admin_client(admin_user):
    """Fixture for an authenticated API client (admin)."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def patient_client(patient_user):
    """Fixture for an authenticated API client (patient)."""
    client = APIClient()
    client.force_authenticate(user=patient_user)
    return client


# --- Mocks ---


@pytest.fixture(autouse=True)
def mock_cache(settings):
    """Use LocMemCache for tests to avoid Redis dependency and state leakage."""
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }


@pytest.fixture(autouse=True)
def mock_rabbitmq(monkeypatch):
    """Mock RabbitMQ to prevent external networking."""
    mock_pika = MagicMock()
    monkeypatch.setattr("pika.BlockingConnection", MagicMock())
    monkeypatch.setattr("api.events.access.get_producer", lambda: MagicMock())
    return mock_pika


@pytest.fixture(autouse=True)
def mock_ai_providers(monkeypatch):
    """
    Disable real AI provider calls globally.
    Mock the factory functions that return AI services.
    """
    # Create mock services with realistic return values
    mock_translation_service = MagicMock()
    mock_translation_service.translate.return_value = "Translated text"
    mock_translation_service.batch_translate.return_value = ["Translated text 1", "Translated text 2"]

    mock_embedding_service = MagicMock()
    mock_embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3, 0.4, 0.5] * 100
    mock_embedding_service.generate_embeddings.return_value = [[0.1, 0.2, 0.3] * 100, [0.4, 0.5, 0.6] * 100]

    mock_transcription_service = MagicMock()
    mock_transcription_service.transcribe.return_value = "Transcribed audio text"

    mock_completion_service = MagicMock()
    mock_completion_service.complete.return_value = "AI completion response"
    mock_completion_service.generate_response.return_value = "AI generated response"

    # Mock AI factory functions
    monkeypatch.setattr(
        "api.services.ai.factory.get_translation_service", lambda *args, **kwargs: mock_translation_service
    )
    monkeypatch.setattr("api.services.ai.get_translation_service", lambda *args, **kwargs: mock_translation_service)
    monkeypatch.setattr(
        "api.services.ai.factory.get_embedding_service", lambda *args, **kwargs: mock_embedding_service
    )
    monkeypatch.setattr("api.services.ai.get_embedding_service", lambda *args, **kwargs: mock_embedding_service)
    monkeypatch.setattr(
        "api.services.ai.factory.get_transcription_service", lambda *args, **kwargs: mock_transcription_service
    )
    monkeypatch.setattr(
        "api.services.ai.get_transcription_service", lambda *args, **kwargs: mock_transcription_service
    )
    monkeypatch.setattr(
        "api.services.ai.factory.get_completion_service", lambda *args, **kwargs: mock_completion_service
    )
    monkeypatch.setattr("api.services.ai.get_completion_service", lambda *args, **kwargs: mock_completion_service)

    return {
        "translation": mock_translation_service,
        "embedding": mock_embedding_service,
        "transcription": mock_transcription_service,
        "completion": mock_completion_service,
    }
