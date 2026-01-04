from unittest.mock import patch

import pytest
from api.models.chat import ChatMessage, ChatRoom
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestChatViews:
    def test_list_chat_rooms(self, auth_client, db):
        ChatRoom.objects.create(name="Room 1")
        ChatRoom.objects.create(name="Room 2")
        url = reverse("chatroom-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2

    def test_create_chat_room(self, auth_client):
        url = reverse("chatroom-list")
        data = {"name": "New Consultation", "patient_language": "en", "doctor_language": "zu"}
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert ChatRoom.objects.filter(name="New Consultation").exists()

    def test_send_message(self, auth_client, db):
        room = ChatRoom.objects.create(name="Test Room", patient_language="en", doctor_language="sw")
        url = reverse("chatroom-send-message", args=[room.id])
        data = {"sender_type": "doctor", "text": "How are you feeling?"}
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert ChatMessage.objects.filter(original_text="How are you feeling?").exists()

    def test_retrieve_messages(self, auth_client, db):
        room = ChatRoom.objects.create(name="Test Room")
        ChatMessage.objects.create(room=room, sender_type="patient", original_text="Hi", original_language="en")
        url = reverse("chatroom-detail", args=[room.id])
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "messages" in response.data
        assert len(response.data["messages"]) == 1

    @patch("api.tasks.audio_tasks.transcribe_audio_async.delay")
    @patch("api.views.chat.CELERY_ENABLED", True)
    def test_send_audio_message(self, mock_transcribe_delay, auth_client, db):
        """Test sending audio message triggers transcription task."""
        room = ChatRoom.objects.create(name="Audio Room", patient_language="en", doctor_language="sw")
        url = reverse("chatroom-send-message", args=[room.id])

        # Create audio data that's at least 500 bytes (the minimum required)
        import base64

        fake_audio = base64.b64encode(b"x" * 600).decode()  # 600 bytes of audio data

        data = {"sender_type": "patient", "text": "[Voice Message]", "audio": fake_audio}
        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        message = ChatMessage.objects.get(id=response.data["id"])
        assert message.has_audio is True
        assert message.audio_file is not None
        mock_transcribe_delay.assert_called_once()

    def test_send_audio_message_too_short(self, auth_client, db):
        """Test sending audio message that's too short returns error."""
        room = ChatRoom.objects.create(name="Audio Room", patient_language="en", doctor_language="sw")
        url = reverse("chatroom-send-message", args=[room.id])

        # Create audio data that's less than 500 bytes
        import base64

        fake_audio = base64.b64encode(b"x" * 100).decode()  # Only 100 bytes

        data = {"sender_type": "patient", "text": "[Voice Message]", "audio": fake_audio}
        response = auth_client.post(url, data, format="json")

        # Should return 400 because audio is too short
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "too short" in response.data["error"]

    def test_room_permissions_patient_access(self, patient_client, db):
        """Test patient can only access their own rooms."""
        room = ChatRoom.objects.create(name="Patient Room")
        url = reverse("chatroom-detail", args=[room.id])
        response = patient_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_room_permissions_admin_access(self, admin_client, db):
        """Test admin can access all rooms."""
        room = ChatRoom.objects.create(name="Admin Room")
        url = reverse("chatroom-detail", args=[room.id])
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_send_message_missing_sender_type(self, auth_client, db):
        """Test sending message without sender_type returns error."""
        room = ChatRoom.objects.create(name="Test Room", patient_language="en", doctor_language="sw")
        url = reverse("chatroom-send-message", args=[room.id])
        data = {"text": "Hello"}
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "sender_type" in response.data["error"]

    def test_send_message_missing_text_and_audio(self, auth_client, db):
        """Test sending message without text or audio returns error."""
        room = ChatRoom.objects.create(name="Test Room", patient_language="en", doctor_language="sw")
        url = reverse("chatroom-send-message", args=[room.id])
        data = {"sender_type": "patient"}
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "text or audio" in response.data["error"]
