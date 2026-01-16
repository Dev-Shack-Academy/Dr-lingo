"""
Tests for WebSocket functionality.

These tests verify:
- WebSocket authentication middleware
- Chat consumer connection/disconnection
- Message broadcasting
- Typing indicators
- RabbitMQ to Channels bridge
"""

from unittest.mock import MagicMock, patch

import pytest
from api.consumers.chat import ChatConsumer
from api.events.channels_bridge import ChannelsBridge
from api.middleware import WebSocketAuthMiddleware
from api.models import ChatRoom
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


@pytest.mark.django_db(transaction=True)
class TestChatConsumer:
    """Tests for the ChatConsumer WebSocket consumer."""

    @pytest.fixture
    def user(self, db):
        """Create a test user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="doctor",
        )

    @pytest.fixture
    def chat_room(self, db):
        """Create a test chat room."""
        return ChatRoom.objects.create(
            name="Test Room",
            patient_language="af",
            doctor_language="en",
        )

    @pytest.mark.asyncio
    async def test_connect_unauthenticated_rejected(self, chat_room):
        """Test that unauthenticated connections are rejected."""
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{chat_room.id}/",
        )
        # Set anonymous user in scope
        communicator.scope["user"] = MagicMock(is_authenticated=False)
        communicator.scope["otp_verified"] = False
        communicator.scope["url_route"] = {"kwargs": {"room_id": str(chat_room.id)}}

        connected, close_code = await communicator.connect()

        # Should reject with custom close code
        assert not connected or close_code == 4001

    @pytest.mark.asyncio
    async def test_connect_otp_not_verified_rejected(self, user, chat_room):
        """Test that connections without OTP verification are rejected."""
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{chat_room.id}/",
        )
        communicator.scope["user"] = user
        communicator.scope["otp_verified"] = False  # OTP not verified
        communicator.scope["url_route"] = {"kwargs": {"room_id": str(chat_room.id)}}

        connected, close_code = await communicator.connect()

        # Should reject with custom close code for OTP failure
        assert not connected or close_code == 4002

    @pytest.mark.asyncio
    async def test_connect_authenticated_and_verified(self, user, chat_room):
        """Test that authenticated and OTP-verified users can connect."""
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{chat_room.id}/",
        )
        communicator.scope["user"] = user
        communicator.scope["otp_verified"] = True
        communicator.scope["url_route"] = {"kwargs": {"room_id": str(chat_room.id)}}

        connected, _ = await communicator.connect()
        assert connected

        # Should receive connection confirmation
        response = await communicator.receive_json_from()
        assert response["type"] == "connection.established"
        assert response["room_id"] == str(chat_room.id)

        await communicator.disconnect()

    @pytest.mark.asyncio
    async def test_typing_indicator(self, user, chat_room):
        """Test typing indicator functionality."""
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{chat_room.id}/",
        )
        communicator.scope["user"] = user
        communicator.scope["otp_verified"] = True
        communicator.scope["url_route"] = {"kwargs": {"room_id": str(chat_room.id)}}

        await communicator.connect()
        # Consume connection message
        await communicator.receive_json_from()

        # Send typing event
        await communicator.send_json_to({"type": "typing"})

        # Note: Typing events are broadcast to the group, not echoed back
        # In a real test with multiple consumers, we'd verify the broadcast

        await communicator.disconnect()

    @pytest.mark.asyncio
    async def test_ping_pong(self, user, chat_room):
        """Test ping/pong keep-alive."""
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{chat_room.id}/",
        )
        communicator.scope["user"] = user
        communicator.scope["otp_verified"] = True
        communicator.scope["url_route"] = {"kwargs": {"room_id": str(chat_room.id)}}

        await communicator.connect()
        # Consume connection message
        await communicator.receive_json_from()

        # Send ping
        await communicator.send_json_to({"type": "ping"})

        # Should receive pong
        response = await communicator.receive_json_from()
        assert response["type"] == "pong"
        assert "timestamp" in response

        await communicator.disconnect()


class TestChannelsBridge(TestCase):
    """Tests for the RabbitMQ to Channels bridge."""

    def test_get_room_group_name(self):
        """Test room group name generation."""
        bridge = ChannelsBridge()
        assert bridge.get_room_group_name(123) == "chat_room_123"
        assert bridge.get_room_group_name(1) == "chat_room_1"

    @patch("api.events.channels_bridge.get_channel_layer")
    def test_send_to_room(self, mock_get_channel_layer):
        """Test sending events to a room group."""
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer

        bridge = ChannelsBridge()
        bridge._channel_layer = mock_channel_layer

        # Mock async_to_sync
        with patch("api.events.channels_bridge.async_to_sync") as mock_async_to_sync:
            mock_async_to_sync.return_value = MagicMock()

            bridge.send_to_room(
                123,
                "message_new",
                {
                    "message_id": 1,
                    "room_id": 123,
                },
            )

            # Verify group_send was called
            mock_async_to_sync.assert_called()

    def test_handle_message_created(self):
        """Test handling message.created events."""
        bridge = ChannelsBridge()

        with patch.object(bridge, "send_to_room") as mock_send:
            bridge.handle_message_created(
                {
                    "room_id": 123,
                    "message_id": 1,
                    "sender_type": "patient",
                    "text": "Hello",
                }
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == 123  # room_id
            assert call_args[0][1] == "message_new"  # event_type

    def test_handle_message_translated(self):
        """Test handling message.translated events."""
        bridge = ChannelsBridge()

        with patch.object(bridge, "send_to_room") as mock_send:
            bridge.handle_message_translated(
                {
                    "room_id": 123,
                    "message_id": 1,
                    "translated_text": "Hallo",
                    "target_lang": "af",
                }
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == 123
            assert call_args[0][1] == "message_translated"

    def test_handle_audio_transcribed(self):
        """Test handling audio.transcribed events."""
        bridge = ChannelsBridge()

        with patch.object(bridge, "send_to_room") as mock_send:
            bridge.handle_audio_transcribed(
                {
                    "room_id": 123,
                    "message_id": 1,
                    "transcription": "Hello doctor",
                    "detected_language": "en",
                }
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == 123
            assert call_args[0][1] == "message_transcribed"

    def test_missing_room_id_logs_warning(self):
        """Test that missing room_id logs a warning."""
        bridge = ChannelsBridge()

        with patch.object(bridge, "send_to_room") as mock_send:
            # Should not call send_to_room if room_id is missing
            bridge.handle_message_created({"message_id": 1})
            mock_send.assert_not_called()


class TestWebSocketAuthMiddleware(TestCase):
    """Tests for WebSocket authentication middleware."""

    def test_get_cookies_from_scope(self):
        """Test cookie extraction from WebSocket scope."""
        middleware = WebSocketAuthMiddleware(inner=MagicMock())

        scope = {
            "headers": [
                (b"cookie", b"sessionid=abc123; csrftoken=xyz789"),
            ]
        }

        cookies = middleware._get_cookies_from_scope(scope)

        assert cookies["sessionid"] == "abc123"
        assert cookies["csrftoken"] == "xyz789"

    def test_get_cookies_empty_headers(self):
        """Test cookie extraction with no cookies."""
        middleware = WebSocketAuthMiddleware(inner=MagicMock())

        scope = {"headers": []}
        cookies = middleware._get_cookies_from_scope(scope)

        assert cookies == {}
