"""
Event Bus Package for Medical Translation System.

This package provides event-driven communication using RabbitMQ.

Events allow different parts of the system to communicate without
tight coupling. When something happens (e.g., message translated),
an event is published and any interested service can react.

Event Types:
- message.created: New message sent
- message.translated: Translation completed
- audio.transcribed: Audio transcription completed
- document.processed: RAG document processed
- doctor_assistance.generated: AI assistance ready

Architecture:
- BusRegistry: Process-local registry for message bus configuration
- MessageBusFactory: Factory for creating producers/consumers
- Producers: Thread-safe message publishing with retry logic
- Consumers: Topic-based subscriptions with handlers
- Access: Singleton access to producer/consumer instances
"""

from .access import get_consumer, get_producer, reset_singletons
from .bus_registry import BusRegistry
from .events import (
    AUDIO_TRANSCRIBED,
    DOCTOR_ASSISTANCE_GENERATED,
    DOCUMENT_PROCESSED,
    MESSAGE_CREATED,
    MESSAGE_TRANSLATED,
)
from .message_bus_factory import MessageBusFactory
from .publisher import (
    emit_audio_transcribed,
    emit_message_created,
    emit_message_translated,
    publish_event,
    publish_event_async,
)
from .subscriber import EventHandler, subscribe

__all__ = [
    # Core components
    "BusRegistry",
    "MessageBusFactory",
    "get_producer",
    "get_consumer",
    "reset_singletons",
    # Publishing
    "publish_event",
    "publish_event_async",
    "emit_message_created",
    "emit_message_translated",
    "emit_audio_transcribed",
    # Subscribing
    "subscribe",
    "EventHandler",
    # Event types
    "MESSAGE_CREATED",
    "MESSAGE_TRANSLATED",
    "AUDIO_TRANSCRIBED",
    "DOCUMENT_PROCESSED",
    "DOCTOR_ASSISTANCE_GENERATED",
]
