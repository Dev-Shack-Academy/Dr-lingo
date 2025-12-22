"""
Event Subscriber.

Subscribes to RabbitMQ events and handles them.
Used by background workers to react to system events.
"""

import logging
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Registry of event handlers
_handlers: dict[str, list[Callable]] = {}


class EventHandler:
    """
    Base class for event handlers.

    Subclass this to create handlers for specific events.

    Example:
        class MessageTranslatedHandler(EventHandler):
            event_type = "message.translated"

            def handle(self, payload):
                # Send WebSocket notification
                notify_user(payload["room_id"], payload["translated_text"])
    """

    event_type: str = None

    def handle(self, payload: dict[str, Any]):
        """Handle the event. Override in subclass."""
        raise NotImplementedError

    def __init__(self):
        if self.event_type:
            register_handler(self.event_type, self.handle)


def subscribe(event_type: str):
    """
    Decorator to register a function as an event handler.

    Example:
        @subscribe("message.translated")
        def handle_translation(payload):
            print(f"Message {payload['message_id']} translated")
    """

    def decorator(func: Callable):
        register_handler(event_type, func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def register_handler(event_type: str, handler: Callable):
    """Register a handler for an event type."""
    if event_type not in _handlers:
        _handlers[event_type] = []

    _handlers[event_type].append(handler)
    logger.debug(f"Registered handler for {event_type}: {handler.__name__}")


def get_handlers(event_type: str) -> list[Callable]:
    """Get all handlers for an event type."""
    # Exact match
    handlers = _handlers.get(event_type, [])

    # Wildcard handlers (e.g., "message.*" matches "message.created")
    for pattern, pattern_handlers in _handlers.items():
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            if event_type.startswith(prefix):
                handlers.extend(pattern_handlers)

    return handlers


def dispatch_event(event_type: str, payload: dict[str, Any]):
    """
    Dispatch an event to all registered handlers.

    Called by the event consumer when a message is received.
    """
    handlers = get_handlers(event_type)

    if not handlers:
        logger.debug(f"No handlers for event: {event_type}")
        return

    for handler in handlers:
        try:
            handler(payload)
        except Exception as e:
            logger.error(f"Handler {handler.__name__} failed for {event_type}: {e}")


def start_consumer():
    """
    Start consuming events from RabbitMQ using the new consumer pattern.

    This should be run in a separate process/thread.
    Typically called from a management command.
    """
    from .access import get_consumer

    consumer = get_consumer()

    if consumer is None:
        logger.error("Message bus not configured, cannot start consumer")
        return

    try:
        # Connect to RabbitMQ
        consumer.connect()

        # Subscribe to all registered event types
        for event_type in _handlers.keys():
            consumer.subscribe(topic=event_type, handler=lambda msg, et=event_type: dispatch_event(et, msg))

        # Also subscribe to wildcard for catch-all
        consumer.subscribe(topic="#", handler=lambda msg: _handle_wildcard_message(msg))

        logger.info("Event consumer started, waiting for events...")
        consumer.run_forever()

    except Exception as e:
        logger.error(f"Event consumer failed: {e}")
    finally:
        try:
            consumer.disconnect()
        except Exception:
            pass


def _handle_wildcard_message(message: dict[str, Any]):
    """Handle messages received via wildcard subscription."""
    event_type = message.get("event_type")
    payload = message.get("payload", {})
    if event_type:
        dispatch_event(event_type, payload)


# Built-in handlers for common events
@subscribe("message.translated")
def log_translation(payload):
    """Log translation events."""
    logger.info(f"Message {payload.get('message_id')} translated to " f"{payload.get('target_lang')}")


@subscribe("audio.transcribed")
def log_transcription(payload):
    """Log transcription events."""
    logger.info(
        f"Audio transcribed for message {payload.get('message_id')}: " f"{payload.get('transcription', '')[:50]}..."
    )
