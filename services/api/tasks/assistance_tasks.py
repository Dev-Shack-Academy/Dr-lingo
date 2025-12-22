import logging
from datetime import datetime

from django.core.cache import cache

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    queue="assistance",
)
def generate_doctor_assistance_async(self, room_id: int, request_type: str = "general"):
    """
    Generate AI-powered assistance for doctors in the background.

    This task:
    1. Gathers conversation context
    2. Queries RAG for patient information
    3. Generates culturally-aware suggestions
    4. Stores assistance in RAG for future reference
    5. Publishes event for real-time notification

    Args:
        room_id: ID of the ChatRoom
        request_type: Type of assistance (general, cultural, medical, followup)

    Returns:
        dict with assistance result
    """
    from api.events import publish_event
    from api.models import ChatRoom
    from api.services.rag_service import RAGService

    logger.info(f"Generating doctor assistance for room {room_id}")

    try:
        room = ChatRoom.objects.get(id=room_id)

        if not room.rag_collection:
            return {
                "status": "no_collection",
                "message": "No RAG collection configured",
            }

        # Get recent conversation
        recent_messages = room.messages.order_by("-created_at")[:10]
        conversation_context = "\n".join(
            [f"{msg.sender_type}: {msg.original_text}" for msg in reversed(list(recent_messages))]
        )

        # Build assistance query based on type
        if request_type == "cultural":
            query = f"""
Provide cultural context and communication tips for this conversation:

Patient Language: {room.patient_language}
Doctor Language: {room.doctor_language}

Conversation:
{conversation_context}

Focus on:
1. Cultural sensitivities
2. Communication style preferences
3. Potential misunderstandings
4. Appropriate phrasing suggestions
"""
        elif request_type == "medical":
            query = f"""
Provide medical context assistance for this conversation:

Conversation:
{conversation_context}

Focus on:
1. Relevant medical history from patient profile
2. Important follow-up questions
3. Symptoms to clarify
4. Medical terminology explanations
"""
        elif request_type == "followup":
            query = f"""
Suggest follow-up questions for this conversation:

Patient Language: {room.patient_language}
Conversation:
{conversation_context}

Provide:
1. 3-5 culturally-appropriate follow-up questions
2. Questions in both {room.doctor_language} and {room.patient_language}
3. Explanation of why each question is important
"""
        else:  # general
            query = f"""
Provide comprehensive assistance for this medical conversation:

Patient Language: {room.patient_language}
Doctor Language: {room.doctor_language}

Conversation:
{conversation_context}

Please suggest:
1. Important follow-up questions considering cultural context
2. Potential communication barriers to clarify
3. Cultural sensitivities to be aware of
4. Relevant medical information from patient history
"""

        # Query RAG and generate assistance
        rag_service = RAGService(room.rag_collection)
        result = rag_service.query_and_answer(query, top_k=5)

        if result["status"] != "success":
            raise Exception(result.get("message", "RAG query failed"))

        assistance = result["answer"]
        sources = result.get("sources", [])

        # Store assistance in RAG for future reference
        assistance_doc = f"""
DOCTOR ASSISTANCE SESSION
Date: {datetime.now().isoformat()}
Room: {room.name}
Patient: {room.patient_name or "Unknown"}
Request Type: {request_type}

CONVERSATION CONTEXT:
{conversation_context}

AI SUGGESTIONS:
{assistance}

SOURCES USED:
{', '.join([s.get('name', 'Unknown') for s in sources])}
"""

        try:
            rag_service.add_document(
                name=f"Assistance Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                content=assistance_doc,
                description=f"Doctor assistance session for {room.name}",
                metadata={
                    "type": "assistance_session",
                    "room_id": room.id,
                    "request_type": request_type,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            logger.warning(f"Failed to store assistance in RAG: {e}")

        # Publish event for real-time notification
        publish_event(
            "doctor_assistance.generated",
            {
                "room_id": room_id,
                "request_type": request_type,
                "assistance": assistance,
                "sources": sources,
            },
        )

        logger.info(f"Doctor assistance generated for room {room_id}")

        return {
            "status": "success",
            "room_id": room_id,
            "assistance": assistance,
            "sources": sources,
        }

    except ChatRoom.DoesNotExist:
        logger.error(f"Room {room_id} not found")
        return {"status": "error", "error": "Room not found"}

    except Exception as e:
        logger.error(f"Assistance generation failed for room {room_id}: {e}")
        raise self.retry(exc=e)


@shared_task(queue="assistance")
def generate_cultural_tips(patient_language: str, doctor_language: str):
    """
    Generate general cultural communication tips.

    Useful for onboarding new doctors or general guidance.
    """
    from api.services.gemini_service import get_gemini_service

    cache_key = f"cultural_tips:{patient_language}:{doctor_language}"
    cached = cache.get(cache_key)

    if cached:
        return {"status": "cached", "tips": cached}

    gemini = get_gemini_service()

    prompt = f"""
Provide cultural communication tips for a doctor who speaks {doctor_language}
communicating with a patient who speaks {patient_language}.

Include:
1. Greeting and address preferences
2. Communication style (direct vs indirect)
3. Topics to approach sensitively
4. Non-verbal communication considerations
5. Common misunderstandings to avoid

Format as a concise, actionable guide.
"""

    # Generate tips using Gemini
    try:
        tips = gemini.generate_text(prompt)
    except Exception:
        # Fallback if generation fails
        tips = f"Cultural tips for {patient_language} <-> {doctor_language} communication"

    cache.set(cache_key, tips, timeout=86400)  # 24 hours

    return {"status": "success", "tips": tips}
