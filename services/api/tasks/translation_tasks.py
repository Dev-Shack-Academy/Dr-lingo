import hashlib
import logging

from django.core.cache import cache

from celery import shared_task

logger = logging.getLogger(__name__)


def get_translation_cache_key(text: str, source_lang: str, target_lang: str) -> str:
    """Generate a unique cache key for translation."""
    content = f"{text}:{source_lang}:{target_lang}"
    return f"translation:{hashlib.sha256(content.encode()).hexdigest()[:16]}"


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    queue="translation",
)
def translate_text_async(
    self,
    message_id: int,
    text: str,
    source_lang: str,
    target_lang: str,
    use_rag: bool = True,
):
    """
    Translate text in the background with caching.

    This task:
    1. Checks Redis cache for existing translation
    2. If not cached, queries RAG for context
    3. Translates with Gemini/Ollama
    4. Caches the result
    5. Updates the message
    6. Publishes event

    Args:
        message_id: ID of the ChatMessage to update
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code
        use_rag: Whether to use RAG context

    Returns:
        dict with translation result
    """
    from api.events import publish_event
    from api.models import ChatMessage
    from api.services.gemini_service import get_gemini_service
    from api.services.rag_service import get_translation_context

    logger.info(f"Starting translation for message {message_id}")

    try:
        message = ChatMessage.objects.get(id=message_id)

        # Check cache first
        cache_key = get_translation_cache_key(text, source_lang, target_lang)
        cached_translation = cache.get(cache_key)

        if cached_translation:
            logger.info(f"Cache hit for translation {message_id}")
            translated_text = cached_translation
        else:
            # Get combined RAG context (knowledge base + patient context)
            rag_context = None
            if use_rag:
                try:
                    context_data = get_translation_context(message.room_id, text, top_k=5)
                    if context_data["has_context"]:
                        # Build context string from knowledge base and patient context
                        context_parts = []

                        if context_data["knowledge_base"]:
                            kb_text = "\n".join(
                                [
                                    f"[{item['name']}]: {item['content'][:300]}"
                                    for item in context_data["knowledge_base"][:3]
                                ]
                            )
                            context_parts.append(f"Reference Information:\n{kb_text}")

                        if context_data["patient_context"]:
                            patient_text = "\n".join(
                                [f"[{item['name']}]: {item['content']}" for item in context_data["patient_context"]]
                            )
                            context_parts.append(f"Patient Context:\n{patient_text}")

                        rag_context = "\n\n".join(context_parts)
                        logger.info(f"RAG context retrieved for message {message_id}")
                except Exception as e:
                    logger.warning(f"RAG query failed: {e}")

            # Get conversation history
            recent_messages = message.room.messages.order_by("-created_at")[:5]
            history = [
                {"sender_type": msg.sender_type, "text": msg.original_text} for msg in reversed(list(recent_messages))
            ]

            # Translate
            gemini = get_gemini_service()
            translated_text = gemini.translate_with_context(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                conversation_history=history,
                sender_type=message.sender_type,
                rag_context=rag_context,
            )

            # Cache the result (1 hour)
            cache.set(cache_key, translated_text, timeout=3600)

        # Update message
        message.translated_text = translated_text
        message.translated_language = target_lang
        message.save()

        # Publish event
        publish_event(
            "message.translated",
            {
                "message_id": message_id,
                "room_id": message.room_id,
                "sender_type": message.sender_type,
                "translated_text": translated_text,
                "target_lang": target_lang,
            },
        )

        logger.info(f"Translation completed for message {message_id}")

        return {
            "status": "success",
            "message_id": message_id,
            "translated_text": translated_text,
            "cached": cached_translation is not None,
        }

    except ChatMessage.DoesNotExist:
        logger.error(f"Message {message_id} not found")
        return {"status": "error", "error": "Message not found"}

    except Exception as e:
        logger.error(f"Translation failed for message {message_id}: {e}")
        raise self.retry(exc=e)


@shared_task(queue="translation")
def batch_translate(translations: list[dict]):
    """
    Batch translate multiple texts.

    Args:
        translations: List of dicts with text, source_lang, target_lang

    Returns:
        List of translation results
    """
    results = []

    for item in translations:
        cache_key = get_translation_cache_key(item["text"], item["source_lang"], item["target_lang"])

        cached = cache.get(cache_key)
        if cached:
            results.append(
                {
                    "text": item["text"],
                    "translation": cached,
                    "cached": True,
                }
            )
        else:
            # Queue individual translation
            # In production, you might want to batch API calls
            results.append(
                {
                    "text": item["text"],
                    "status": "queued",
                }
            )

    return results
