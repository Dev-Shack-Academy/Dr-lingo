import logging

from django.core.cache import cache

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3,
    queue="audio",
)
def transcribe_audio_async(self, message_id: int, audio_data: bytes, source_lang: str):
    """
    Transcribe audio in the background.

    This task:
    1. Receives audio data and message ID
    2. Transcribes using Gemini/Whisper
    3. Updates the message with transcription
    4. Triggers translation task
    5. Publishes event via RabbitMQ

    Args:
        message_id: ID of the ChatMessage to update
        audio_data: Raw audio bytes
        source_lang: Source language code

    Returns:
        dict with transcription result
    """
    from api.events import publish_event
    from api.models import ChatMessage
    from api.services.gemini_service import get_gemini_service

    logger.info(f"Starting audio transcription for message {message_id}")

    try:
        # Get the message
        message = ChatMessage.objects.get(id=message_id)

        # Check cache first
        cache_key = f"transcription:{hash(audio_data)}"
        cached_result = cache.get(cache_key)

        if cached_result:
            logger.info(f"Cache hit for transcription {message_id}")
            transcription = cached_result
        else:
            # Transcribe with Gemini
            gemini = get_gemini_service()
            result = gemini.transcribe_audio(audio_data, source_lang)

            if not result["success"]:
                raise Exception(result.get("error", "Transcription failed"))

            transcription = result["transcription"]

            # Cache the result (1 hour)
            cache.set(cache_key, transcription, timeout=3600)

        # Update message
        message.audio_transcription = transcription
        message.original_text = transcription
        message.save()

        # Publish event
        publish_event(
            "audio.transcribed",
            {
                "message_id": message_id,
                "room_id": message.room_id,
                "transcription": transcription,
                "source_lang": source_lang,
            },
        )

        # Trigger translation task
        from api.tasks.translation_tasks import translate_text_async

        target_lang = (
            message.room.doctor_language if message.sender_type == "patient" else message.room.patient_language
        )

        translate_text_async.delay(
            message_id=message_id,
            text=transcription,
            source_lang=source_lang,
            target_lang=target_lang,
        )

        logger.info(f"Audio transcription completed for message {message_id}")

        return {
            "status": "success",
            "message_id": message_id,
            "transcription": transcription,
        }

    except ChatMessage.DoesNotExist:
        logger.error(f"Message {message_id} not found")
        return {"status": "error", "error": "Message not found"}

    except Exception as e:
        logger.error(f"Audio transcription failed for message {message_id}: {e}")
        raise self.retry(exc=e)


@shared_task(queue="audio")
def process_audio_file(message_id: int, file_path: str):
    """
    Process and optimize audio file.

    - Convert to standard format
    - Compress if needed
    - Extract metadata
    """
    logger.info(f"Processing audio file for message {message_id}")

    # TODO: Implement audio processing with ffmpeg
    # - Convert to standard format (webm/mp3)
    # - Normalize audio levels
    # - Extract duration metadata

    return {"status": "success", "message_id": message_id}
