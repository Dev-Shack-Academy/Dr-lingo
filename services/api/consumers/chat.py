import json
import logging
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

# Rate limiting for typing events (max 1 event per second per user)
TYPING_RATE_LIMIT_SECONDS = 1.0


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for chat room real-time updates.

    Endpoint: ws://host/ws/chat/{room_id}/

    Events sent to client:
        - message.new: New message created
        - message.translated: Message translation completed
        - message.transcribed: Audio transcription completed
        - user.typing: User started typing
        - user.stopped_typing: User stopped typing
        - tts.generated: TTS audio generated
        - error: Error occurred

    Events received from client:
        - typing: User is typing
        - stop_typing: User stopped typing
        - ping: Keep-alive ping
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = None
        self.room_group_name = None
        self.user = None
        self.last_typing_time = 0
        self._current_sender_type = None

    async def connect(self):
        """
        Handle WebSocket connection.

        Validates:
        1. User is authenticated
        2. OTP verification is complete
        3. User has access to the room
        """
        # Get user from scope (set by WebSocketAuthMiddleware)
        self.user = self.scope.get("user", AnonymousUser())
        otp_verified = self.scope.get("otp_verified", False)

        # Get room ID from URL
        self.room_id = self.scope["url_route"]["kwargs"].get("room_id")

        # Validate authentication
        if not self.user.is_authenticated:
            logger.warning(f"WebSocket connection rejected: unauthenticated user for room {self.room_id}")
            await self.close(code=4001)  # Custom close code for auth failure
            return

        # Validate OTP verification
        if not otp_verified:
            logger.warning(f"WebSocket connection rejected: OTP not verified for user {self.user.email}")
            await self.close(code=4002)  # Custom close code for OTP failure
            return

        # Validate room access
        has_access = await self._check_room_access()
        if not has_access:
            logger.warning(
                f"WebSocket connection rejected: user {self.user.email} has no access to room {self.room_id}"
            )
            await self.close(code=4003)  # Custom close code for access denied
            return

        # Create room group name
        self.room_group_name = f"chat_room_{self.room_id}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()

        logger.info(f"WebSocket connected: user={self.user.email}, room={self.room_id}")

        # Send connection confirmation
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection.established",
                    "room_id": self.room_id,
                    "user_id": self.user.id,
                    "message": "Connected to chat room",
                }
            )
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if self.room_group_name:
            # Leave room group
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

            # Notify room that user disconnected (optional)
            if self.user and self.user.is_authenticated:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "user_disconnected",
                        "user_id": self.user.id,
                        "user_email": self.user.email,
                    },
                )

        logger.info(
            f"WebSocket disconnected: user={getattr(self.user, 'email', 'unknown')}, room={self.room_id}, code={close_code}"
        )

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages from client.

        Supported message types:
        - typing: User started typing
        - stop_typing: User stopped typing
        - ping: Keep-alive ping
        """
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            if message_type == "typing":
                # Store sender_type from client for typing events
                self._current_sender_type = data.get("sender_type")
                await self._handle_typing()
            elif message_type == "stop_typing":
                await self._handle_stop_typing()
            elif message_type == "ping":
                await self._handle_ping()
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data[:100]}")
            await self.send(text_data=json.dumps({"type": "error", "message": "Invalid JSON format"}))
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self.send(text_data=json.dumps({"type": "error", "message": "Error processing message"}))

    # ==================== Client Message Handlers ====================

    async def _handle_typing(self):
        """Handle typing indicator with rate limiting."""
        current_time = time.time()

        # Rate limit typing events
        if current_time - self.last_typing_time < TYPING_RATE_LIMIT_SECONDS:
            return

        self.last_typing_time = current_time

        # Broadcast typing event to room
        # sender_type is set from the client message in receive()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_typing",
                "user_id": self.user.id,
                "user_email": self.user.email,
                "sender_type": self._current_sender_type or getattr(self.user, "role", "unknown"),
            },
        )

    async def _handle_stop_typing(self):
        """Handle stop typing indicator."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_stopped_typing",
                "user_id": self.user.id,
                "user_email": self.user.email,
            },
        )

    async def _handle_ping(self):
        """Handle keep-alive ping."""
        await self.send(text_data=json.dumps({"type": "pong", "timestamp": time.time()}))

    # ==================== Group Message Handlers ====================
    # These methods are called when messages are sent to the group

    async def message_new(self, event):
        """Handle new message event from RabbitMQ bridge."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message.new",
                    "message_id": event.get("message_id"),
                    "room_id": event.get("room_id"),
                    "sender_type": event.get("sender_type"),
                    "original_text": event.get("original_text"),
                    "has_audio": event.get("has_audio", False),
                    "timestamp": event.get("timestamp"),
                }
            )
        )

    async def message_translated(self, event):
        """Handle message translated event from RabbitMQ bridge."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message.translated",
                    "message_id": event.get("message_id"),
                    "room_id": event.get("room_id"),
                    "translated_text": event.get("translated_text"),
                    "target_lang": event.get("target_lang"),
                }
            )
        )

    async def message_transcribed(self, event):
        """Handle audio transcription event from RabbitMQ bridge."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message.transcribed",
                    "message_id": event.get("message_id"),
                    "room_id": event.get("room_id"),
                    "transcription": event.get("transcription"),
                    "detected_language": event.get("detected_language"),
                }
            )
        )

    async def tts_generated(self, event):
        """Handle TTS generation event from RabbitMQ bridge."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "tts.generated",
                    "message_id": event.get("message_id"),
                    "room_id": event.get("room_id"),
                    "audio_url": event.get("audio_url"),
                }
            )
        )

    async def translation_failed(self, event):
        """Handle translation failure event from RabbitMQ bridge."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "translation.failed",
                    "message_id": event.get("message_id"),
                    "room_id": event.get("room_id"),
                    "error": event.get("error"),
                    "error_type": event.get("error_type"),
                }
            )
        )

    async def audio_processing_failed(self, event):
        """Handle audio processing failure event from RabbitMQ bridge."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "audio.processing_failed",
                    "message_id": event.get("message_id"),
                    "room_id": event.get("room_id"),
                    "error": event.get("error"),
                    "error_type": event.get("error_type"),
                }
            )
        )

    async def user_typing(self, event):
        """Handle user typing event."""
        # Don't send typing events back to the sender
        if event.get("user_id") == self.user.id:
            return

        await self.send(
            text_data=json.dumps(
                {
                    "type": "user.typing",
                    "user_id": event.get("user_id"),
                    "sender_type": event.get("sender_type"),
                }
            )
        )

    async def user_stopped_typing(self, event):
        """Handle user stopped typing event."""
        # Don't send to the sender
        if event.get("user_id") == self.user.id:
            return

        await self.send(
            text_data=json.dumps(
                {
                    "type": "user.stopped_typing",
                    "user_id": event.get("user_id"),
                }
            )
        )

    async def user_disconnected(self, event):
        """Handle user disconnection notification."""
        # Don't send to the disconnecting user
        if event.get("user_id") == self.user.id:
            return

        await self.send(
            text_data=json.dumps(
                {
                    "type": "user.disconnected",
                    "user_id": event.get("user_id"),
                }
            )
        )

    # ==================== Helper Methods ====================

    @database_sync_to_async
    def _check_room_access(self) -> bool:
        """Check if user has access to the chat room."""
        try:
            from api.models import ChatRoom

            room = ChatRoom.objects.filter(id=self.room_id).first()
            if not room:
                return False

            # Admins have access to all rooms
            if self.user.role == "admin" or self.user.is_superuser:
                return True

            # For now, allow all authenticated users
            # In production, you might want to check room membership
            return True

        except Exception as e:
            logger.error(f"Error checking room access: {e}")
            return False
