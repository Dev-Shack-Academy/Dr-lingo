"""
Event Type Definitions.

Defines all event types used in the system.
Each event has a name and expected payload structure.
"""

# Message Events
MESSAGE_CREATED = "message.created"
MESSAGE_TRANSLATED = "message.translated"
MESSAGE_UPDATED = "message.updated"
MESSAGE_DELETED = "message.deleted"

# Audio Events
AUDIO_RECEIVED = "audio.received"
AUDIO_TRANSCRIBED = "audio.transcribed"
AUDIO_PROCESSING_FAILED = "audio.processing_failed"

# RAG Events
DOCUMENT_ADDED = "document.added"
DOCUMENT_PROCESSED = "document.processed"
DOCUMENT_DELETED = "document.deleted"
COLLECTION_CREATED = "collection.created"
COLLECTION_REINDEXED = "collection.reindexed"

# Doctor Assistance Events
DOCTOR_ASSISTANCE_REQUESTED = "doctor_assistance.requested"
DOCTOR_ASSISTANCE_GENERATED = "doctor_assistance.generated"

# User Events
USER_JOINED_ROOM = "user.joined_room"
USER_LEFT_ROOM = "user.left_room"
USER_TYPING = "user.typing"

# System Events
SYSTEM_HEALTH_CHECK = "system.health_check"
CACHE_CLEARED = "cache.cleared"


# Event Payload Schemas (for documentation)
EVENT_SCHEMAS = {
    MESSAGE_CREATED: {
        "message_id": "int",
        "room_id": "int",
        "sender_type": "str (patient|doctor)",
        "original_text": "str",
        "has_audio": "bool",
    },
    MESSAGE_TRANSLATED: {
        "message_id": "int",
        "room_id": "int",
        "sender_type": "str",
        "translated_text": "str",
        "target_lang": "str",
    },
    AUDIO_TRANSCRIBED: {
        "message_id": "int",
        "room_id": "int",
        "transcription": "str",
        "source_lang": "str",
    },
    DOCUMENT_PROCESSED: {
        "document_id": "int",
        "collection_id": "int",
        "name": "str",
    },
    DOCTOR_ASSISTANCE_GENERATED: {
        "room_id": "int",
        "request_type": "str",
        "assistance": "str",
        "sources": "list",
    },
}
