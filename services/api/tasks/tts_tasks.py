import logging
import os

from django.conf import settings
from django.core.files.base import ContentFile

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=2,
    queue="audio",  # Use audio queue for TTS tasks
)
def generate_tts_async(
    self,
    message_id: int,
    text: str,
    language: str,
    speaker_type: str = "default",  # Kept for API compatibility (ignored by Piper)
):
    """
    Generate TTS audio for a message in the background using Piper TTS.

    Args:
        message_id: ID of the ChatMessage to update
        text: Text to synthesize
        language: Target language code
        speaker_type: Legacy param (ignored - Piper uses fixed voices per language)

    Returns:
        dict with TTS result
    """
    from api.models import ChatMessage
    from api.services.tts_service import is_tts_available, text_to_speech

    logger.info(f"Starting TTS generation for message {message_id}")

    # Check if TTS is available
    if not is_tts_available():
        logger.warning(f"TTS not available for message {message_id}, skipping audio generation")
        return {"success": False, "error": "TTS not installed or no voice models found"}

    try:
        message = ChatMessage.objects.get(id=message_id)

        # Skip if text is too short or a placeholder
        if not text or len(text.strip()) < 3:
            return {"success": False, "error": "Text too short"}

        if text.startswith("[") and text.endswith("]"):
            return {"success": False, "error": "Placeholder text"}

        # Generate output path
        output_dir = os.path.join(settings.MEDIA_ROOT, "tts_output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"tts_{message_id}.wav")

        # Generate TTS with speaker type for voice selection
        result = text_to_speech(
            text=text,
            language=language,
            speaker_type=speaker_type,
            output_path=output_path,
        )

        if result["success"]:
            # Read the generated audio file
            with open(output_path, "rb") as f:
                audio_content = f.read()

            # Save to message's tts_audio field
            message.tts_audio.save(
                f"tts_{message_id}.wav",
                ContentFile(audio_content),
                save=True,
            )

            # Publish event for real-time update
            try:
                from api.events import publish_event

                publish_event(
                    "tts.generated",
                    {
                        "message_id": message_id,
                        "room_id": message.room_id,
                        "audio_url": message.tts_audio.url if message.tts_audio else None,
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to publish tts.generated event: {e}")

            # Clean up temp file
            if os.path.exists(output_path):
                os.remove(output_path)

            logger.info(f"TTS generated for message {message_id}")
            return {"success": True, "message_id": message_id}
        else:
            logger.error(f"TTS failed for message {message_id}: {result.get('error')}")
            return result

    except ChatMessage.DoesNotExist:
        logger.error(f"Message {message_id} not found")
        return {"success": False, "error": "Message not found"}
    except Exception as e:
        logger.error(f"TTS task failed: {e}")
        raise  # Let Celery retry
