import hashlib
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
    2. Transcribes using configured AI provider (Gemini/Ollama)
    3. Updates the message with transcription and detected language
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
    from api.services.ai import get_transcription_service

    logger.info(f"Starting audio transcription for message {message_id}")

    try:
        # Get the message
        message = ChatMessage.objects.get(id=message_id)

        # Create a more specific cache key that includes message ID and language
        # This prevents different messages from sharing cached transcriptions
        audio_hash = hashlib.md5(audio_data).hexdigest()
        cache_key = f"transcription:{message_id}:{source_lang}:{audio_hash}"
        cached_result = cache.get(cache_key)

        if cached_result:
            logger.info(f"Cache hit for transcription {message_id}")
            transcription = cached_result["transcription"]
            detected_language = cached_result.get("detected_language", source_lang)
        else:
            # Transcribe using configured AI provider (Gemini or Ollama)
            transcription_service = get_transcription_service()
            result = transcription_service.transcribe(audio_data, source_lang)

            if not result["success"]:
                # Update message with error state
                message.original_text = "[Transcription failed]"
                message.translated_text = f"[Error: {result.get('error', 'Transcription failed')}]"
                message.save()
                raise Exception(result.get("error", "Transcription failed"))

            transcription = result["transcription"]
            detected_language = result.get("detected_language", source_lang)

            # Only cache successful transcriptions with both transcription and language
            cache_data = {"transcription": transcription, "detected_language": detected_language}
            cache.set(cache_key, cache_data, timeout=3600)  # 1 hour

        # Validate transcription
        if not transcription or len(transcription.strip()) == 0:
            message.original_text = "[No speech detected]"
            message.translated_text = "[No speech detected]"
            message.save()
            logger.warning(f"No speech detected in audio for message {message_id}")
            return {"status": "error", "message_id": message_id, "error": "No speech detected"}

        # Update message with transcription and detected language
        message.audio_transcription = transcription
        message.original_text = transcription
        message.original_language = detected_language
        # Set translation status to show it's being translated
        message.translated_text = "[Translating...]"
        message.save()

        logger.info(f"Transcription successful for message {message_id}: '{transcription[:50]}...'")

        # Publish event
        publish_event(
            "audio.transcribed",
            {
                "message_id": message_id,
                "room_id": message.room_id,
                "transcription": transcription,
                "source_lang": detected_language,
                "detected_language": detected_language,
            },
        )

        # Trigger translation task only if message still exists and transcription was successful
        try:
            # Refresh message from database to ensure it still exists
            message.refresh_from_db()

            from api.tasks.translation_tasks import translate_text_async

            target_lang = (
                message.room.doctor_language if message.sender_type == "patient" else message.room.patient_language
            )

            translate_text_async.delay(
                message_id=message_id,
                text=transcription,
                source_lang=detected_language,  # Use detected language, not original source_lang
                target_lang=target_lang,
            )

            logger.info(f"Audio transcription completed for message {message_id}, translation queued")
        except ChatMessage.DoesNotExist:
            logger.warning(f"Message {message_id} was deleted after transcription, skipping translation")
        except Exception as e:
            logger.error(f"Failed to queue translation for message {message_id}: {e}")
            # Don't raise here, transcription was successful

        return {
            "status": "success",
            "message_id": message_id,
            "transcription": transcription,
            "detected_language": detected_language,
        }

    except ChatMessage.DoesNotExist:
        logger.error(f"Message {message_id} not found - may have been deleted due to processing error")
        return {"status": "error", "error": "Message not found"}

    except Exception as e:
        logger.error(f"Audio transcription failed for message {message_id}: {e}")
        # Try to update message with error state before retrying, but don't fail if message is gone
        try:
            message = ChatMessage.objects.get(id=message_id)
            message.original_text = "[Transcription failed]"
            message.translated_text = f"[Error: {str(e)}]"
            message.save()
        except ChatMessage.DoesNotExist:
            logger.warning(f"Message {message_id} was deleted, cannot update error state")
        except Exception as update_error:
            logger.warning(f"Failed to update message {message_id} error state: {update_error}")

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
