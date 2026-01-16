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

# Translation Events
TRANSLATION_FAILED = "translation.failed"

# RAG Events
DOCUMENT_ADDED = "document.added"
DOCUMENT_PROCESSED = "document.processed"
DOCUMENT_DELETED = "document.deleted"
COLLECTION_CREATED = "collection.created"
COLLECTION_REINDEXED = "collection.reindexed"

# Dataset Import Events (Hugging Face)
DATASET_IMPORT_STARTED = "dataset.import_started"
DATASET_IMPORT_COMPLETED = "dataset.import_completed"
DATASET_IMPORT_FAILED = "dataset.import_failed"
DATASET_BATCH_IMPORT_STARTED = "dataset.batch_import_started"

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
    TRANSLATION_FAILED: {
        "message_id": "int",
        "room_id": "int",
        "error": "str",
        "error_type": "str",
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
    DATASET_IMPORT_STARTED: {
        "lang_code": "str",
        "lang_name": "str",
        "collection_name": "str",
        "split": "str",
    },
    DATASET_IMPORT_COMPLETED: {
        "lang_code": "str",
        "lang_name": "str",
        "collection_id": "int",
        "collection_name": "str",
        "created": "int",
        "skipped": "int",
        "errors": "int",
    },
    DATASET_IMPORT_FAILED: {
        "lang_code": "str",
        "lang_name": "str",
        "error": "str",
    },
    DATASET_BATCH_IMPORT_STARTED: {
        "languages": "list[str]",
        "split": "str",
        "limit": "int|None",
    },
}
