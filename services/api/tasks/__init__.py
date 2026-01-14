import logging

from django.conf import settings

from api.events.bus_registry import BusRegistry
from celery.signals import beat_init, worker_process_init, worker_ready

from .assistance_tasks import generate_doctor_assistance_async
from .audio_tasks import transcribe_audio_async
from .cleanup_tasks import cleanup_expired_cache, cleanup_old_audio_files
from .dataset_tasks import import_all_hf_languages, import_hf_dataset_async
from .pdf_tasks import process_pdf_document_async
from .rag_tasks import generate_embeddings_async, process_document_async
from .translation_tasks import translate_text_async
from .tts_tasks import generate_tts_async

logger = logging.getLogger(__name__)


def _register_message_bus() -> None:
    """
    Register the message bus config in this Celery process.

    Called by Celery startup hooks to ensure the BusRegistry is set up
    so that tasks can publish events via get_producer().
    """
    bus_cfg = getattr(settings, "MESSAGE_BUS_CONFIG", None)
    if not bus_cfg:
        logger.debug("No message bus configuration found, skipping registry setup")
        return

    backend = bus_cfg.get("backend")
    if not backend:
        logger.warning("MESSAGE_BUS_CONFIG missing 'backend' key")
        return

    if BusRegistry.is_configured():
        logger.debug("Message bus already configured for this process")
        return

    BusRegistry.set(backend=backend, config=bus_cfg.get(backend, {}))
    logger.info(f"Registered message bus config for backend {backend} (Celery context)")


@worker_ready.connect
def _on_worker_ready(**kwargs):
    """Register message bus when worker is ready."""
    _register_message_bus()


@worker_process_init.connect
def _on_worker_process_init(**_):
    """Register message bus when worker process initializes."""
    _register_message_bus()


@beat_init.connect
def _on_beat_init(**_):
    """Register message bus when beat scheduler initializes."""
    _register_message_bus()


__all__ = [
    "transcribe_audio_async",
    "translate_text_async",
    "process_document_async",
    "generate_embeddings_async",
    "generate_doctor_assistance_async",
    "cleanup_old_audio_files",
    "cleanup_expired_cache",
    "import_hf_dataset_async",
    "import_all_hf_languages",
    "generate_tts_async",
    "process_pdf_document_async",
]
