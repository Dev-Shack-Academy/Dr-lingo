"""
Event Publisher.

Publishes events to RabbitMQ for consumption by other services.
Supports both synchronous and asynchronous publishing.

Uses the new producer pattern via get_producer() for thread-safe,
connection-pooled publishing with automatic retry on failure.
"""

import json
import logging
from datetime import datetime
from typing import Any

from .access import get_producer

logger = logging.getLogger(__name__)


def publish_event(event_type: str, payload: dict[str, Any]) -> bool:
    """
    Publish an event to RabbitMQ using the producer singleton.

    If RabbitMQ is not available, logs the event instead.

    Args:
        event_type: Type of event (e.g., "message.created")
        payload: Event data dictionary

    Returns:
        True if published successfully, False otherwise

    Example:
        publish_event("message.translated", {
            "message_id": 123,
            "room_id": 456,
            "translated_text": "Hello",
        })
    """
    # Add metadata to payload
    event_data = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "payload": payload,
    }

    # Get the producer singleton
    producer = get_producer()

    if producer is None:
        # Fallback: log the event
        logger.info(f"Event (logged): {event_type} - {json.dumps(payload)}")
        return True

    try:
        # Use the producer to publish
        producer.publish(topic=event_type, message=event_data)
        logger.debug(f"Event published: {event_type}")
        return True

    except Exception as e:
        logger.error(f"Failed to publish event {event_type}: {e}")
        # Fallback: log the event
        logger.info(f"Event (fallback logged): {event_type} - {json.dumps(payload)}")
        return False


def publish_event_async(event_type: str, payload: dict[str, Any]):
    """
    Publish an event asynchronously via Celery task.

    Use this for non-critical events where you don't need
    to wait for confirmation.

    Args:
        event_type: Type of event
        payload: Event data dictionary
    """
    from api.tasks.event_tasks import publish_event_task

    publish_event_task.delay(event_type, payload)


# Convenience functions for common events
def emit_message_created(message_id: int, room_id: int, sender_type: str, text: str, has_audio: bool = False):
    """Emit message.created event."""
    publish_event(
        "message.created",
        {
            "message_id": message_id,
            "room_id": room_id,
            "sender_type": sender_type,
            "original_text": text,
            "has_audio": has_audio,
        },
    )


def emit_message_translated(message_id: int, room_id: int, sender_type: str, translated_text: str, target_lang: str):
    """Emit message.translated event."""
    publish_event(
        "message.translated",
        {
            "message_id": message_id,
            "room_id": room_id,
            "sender_type": sender_type,
            "translated_text": translated_text,
            "target_lang": target_lang,
        },
    )


def emit_audio_transcribed(message_id: int, room_id: int, transcription: str, source_lang: str):
    """Emit audio.transcribed event."""
    publish_event(
        "audio.transcribed",
        {
            "message_id": message_id,
            "room_id": room_id,
            "transcription": transcription,
            "source_lang": source_lang,
        },
    )
