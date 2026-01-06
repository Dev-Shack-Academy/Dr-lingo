"""
RabbitMQ to Django Channels Event Bridge.

This module bridges RabbitMQ events to Django Channels groups,
enabling real-time WebSocket updates for browser clients.

Architecture:
    RabbitMQ Event → Event Handler → Channels Group → WebSocket Consumer → Browser

Usage:
    The bridge is automatically started when the event consumer runs.
    Events are forwarded to the appropriate Channels group based on room_id.
"""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class ChannelsBridge:
    """
    Bridge between RabbitMQ events and Django Channels.

    This class provides methods to forward RabbitMQ events to
    the appropriate Channels groups for real-time WebSocket delivery.
    """

    def __init__(self):
        self._channel_layer = None

    @property
    def channel_layer(self):
        """Lazy load channel layer."""
        if self._channel_layer is None:
            self._channel_layer = get_channel_layer()
        return self._channel_layer

    def get_room_group_name(self, room_id: int) -> str:
        """Get the Channels group name for a chat room."""
        return f"chat_room_{room_id}"

    def send_to_room(self, room_id: int, event_type: str, data: dict):
        """
        Send an event to all WebSocket connections in a room.

        Args:
            room_id: The chat room ID
            event_type: The event type (e.g., 'message_new', 'message_translated')
            data: The event data to send
        """
        try:
            group_name = self.get_room_group_name(room_id)

            # Add the type for Channels routing
            message = {"type": event_type, **data}

            async_to_sync(self.channel_layer.group_send)(group_name, message)
            logger.debug(f"Sent {event_type} to group {group_name}")

        except Exception as e:
            logger.error(f"Error sending to Channels group: {e}")

    # ==================== Event Handlers ====================
    # These methods are called by the RabbitMQ event subscriber

    def handle_message_created(self, event_data: dict):
        """Handle message.created event from RabbitMQ."""
        room_id = event_data.get("room_id")
        if not room_id:
            logger.warning("message.created event missing room_id")
            return

        self.send_to_room(
            room_id,
            "message_new",
            {
                "message_id": event_data.get("message_id"),
                "room_id": room_id,
                "sender_type": event_data.get("sender_type"),
                "original_text": event_data.get("text"),
                "has_audio": event_data.get("has_audio", False),
                "timestamp": event_data.get("timestamp"),
            },
        )

    def handle_message_translated(self, event_data: dict):
        """Handle message.translated event from RabbitMQ."""
        room_id = event_data.get("room_id")
        if not room_id:
            logger.warning("message.translated event missing room_id")
            return

        self.send_to_room(
            room_id,
            "message_translated",
            {
                "message_id": event_data.get("message_id"),
                "room_id": room_id,
                "translated_text": event_data.get("translated_text"),
                "target_lang": event_data.get("target_lang"),
                "sender_type": event_data.get("sender_type"),
            },
        )

    def handle_audio_transcribed(self, event_data: dict):
        """Handle audio.transcribed event from RabbitMQ."""
        room_id = event_data.get("room_id")
        if not room_id:
            logger.warning("audio.transcribed event missing room_id")
            return

        self.send_to_room(
            room_id,
            "message_transcribed",
            {
                "message_id": event_data.get("message_id"),
                "room_id": room_id,
                "transcription": event_data.get("transcription"),
                "detected_language": event_data.get("detected_language"),
                "source_lang": event_data.get("source_lang"),
            },
        )

    def handle_tts_generated(self, event_data: dict):
        """Handle tts.generated event from RabbitMQ."""
        room_id = event_data.get("room_id")
        if not room_id:
            logger.warning("tts.generated event missing room_id")
            return

        self.send_to_room(
            room_id,
            "tts_generated",
            {
                "message_id": event_data.get("message_id"),
                "room_id": room_id,
                "audio_url": event_data.get("audio_url"),
            },
        )


# Global bridge instance
_bridge_instance = None


def get_channels_bridge() -> ChannelsBridge:
    """Get the global ChannelsBridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = ChannelsBridge()
    return _bridge_instance


# ==================== Event Handler Functions ====================
# These functions are registered with the RabbitMQ event subscriber


def forward_message_created(event_data: dict):
    """Forward message.created event to Channels."""
    bridge = get_channels_bridge()
    bridge.handle_message_created(event_data)


def forward_message_translated(event_data: dict):
    """Forward message.translated event to Channels."""
    bridge = get_channels_bridge()
    bridge.handle_message_translated(event_data)


def forward_audio_transcribed(event_data: dict):
    """Forward audio.transcribed event to Channels."""
    bridge = get_channels_bridge()
    bridge.handle_audio_transcribed(event_data)


def forward_tts_generated(event_data: dict):
    """Forward tts.generated event to Channels."""
    bridge = get_channels_bridge()
    bridge.handle_tts_generated(event_data)


def register_channels_handlers():
    """
    Register Channels bridge handlers with the RabbitMQ event subscriber.

    Call this function when starting the event consumer to enable
    real-time WebSocket updates.
    """
    from api.events import register_handler

    # Register handlers for events that should be forwarded to WebSockets
    register_handler("message.created", forward_message_created)
    register_handler("message.translated", forward_message_translated)
    register_handler("audio.transcribed", forward_audio_transcribed)
    register_handler("tts.generated", forward_tts_generated)

    logger.info("Channels bridge handlers registered for WebSocket forwarding")
