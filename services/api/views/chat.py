import base64
import logging

from django.conf import settings
from django.core.files.base import ContentFile
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.models import ChatMessage, ChatRoom, Collection
from api.permissions import CanGetAIAssistance, CanViewPatientContext
from api.serializers import ChatMessageSerializer, ChatRoomListSerializer, ChatRoomSerializer
from api.services.ai import get_transcription_service, get_translation_service
from api.services.rag_service import RAGService

logger = logging.getLogger(__name__)

# Check if Celery is available for async processing
CELERY_ENABLED = getattr(settings, "CELERY_BROKER_URL", None) is not None


class ChatRoomViewSet(viewsets.ModelViewSet):
    """ViewSet for managing chat rooms."""

    queryset = ChatRoom.objects.all()

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ["add_patient_context"]:
            return [IsAuthenticated(), CanViewPatientContext()]
        if self.action in ["get_doctor_assistance"]:
            return [IsAuthenticated(), CanGetAIAssistance()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "list":
            return ChatRoomListSerializer
        return ChatRoomSerializer

    @action(detail=True, methods=["post"])
    def send_message(self, request, pk=None):
        """
        Send a message in a chat room with automatic translation.

        POST /api/chat-rooms/{id}/send_message/
        """
        room = self.get_object()
        sender_type = request.data.get("sender_type")
        text = request.data.get("text")
        image_data = request.data.get("image")
        audio_data = request.data.get("audio")

        if not sender_type:
            return Response({"error": "sender_type is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not text and not audio_data:
            return Response({"error": "Either text or audio is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Determine languages
        if sender_type == "patient":
            original_lang = room.patient_language
            target_lang = room.doctor_language
        else:
            original_lang = room.doctor_language
            target_lang = room.patient_language

        # Get conversation history for context
        recent_messages = room.messages.order_by("-created_at")[:5]
        history = [
            {"sender_type": msg.sender_type, "text": msg.original_text} for msg in reversed(list(recent_messages))
        ]

        # Query RAG for relevant context
        rag_context = self._get_rag_context(room, history, text, sender_type)

        # Translate message with RAG context using AI factory
        try:
            translator = get_translation_service()
            translated_text = translator.translate_with_context(
                text=text,
                source_lang=original_lang,
                target_lang=target_lang,
                conversation_history=history,
                sender_type=sender_type,
                rag_context=rag_context,
            )
        except Exception as e:
            return Response({"error": f"Translation failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Create message
        message = ChatMessage.objects.create(
            room=room,
            sender_type=sender_type,
            original_text=text,
            original_language=original_lang,
            translated_text=translated_text,
            translated_language=target_lang,
            has_image=bool(image_data),
            has_audio=bool(audio_data),
        )

        # Publish message created event (for real-time notifications via RabbitMQ)
        try:
            from api.events import publish_event

            publish_event(
                "message.created",
                {
                    "message_id": message.id,
                    "room_id": room.id,
                    "sender_type": sender_type,
                    "text": text[:100],  # Truncate for event
                    "has_audio": bool(audio_data),
                },
            )
        except Exception as e:
            logger.warning(f"Failed to publish message.created event: {e}")

        # Process audio if provided
        if audio_data:
            result = self._process_audio(message, audio_data, original_lang, target_lang, history, rag_context)
            if result is not None:
                return result

        # Process image if provided
        if image_data:
            self._process_image(message, image_data, target_lang)

        serializer = ChatMessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _get_rag_context(self, room, history, text, sender_type):
        """Get RAG context for translation."""
        if not room.rag_collection:
            return None

        try:
            logger.info(f"RAG collection found: {room.rag_collection.name}")
            conversation_context = "\n".join([f"{h['sender_type']}: {h['text']}" for h in history])

            rag_query = f"""
Context: Medical conversation between patient and doctor.
Patient Language: {room.patient_language}
Doctor Language: {room.doctor_language}
Current Speaker: {sender_type}

Recent Conversation:
{conversation_context}

Current Message: {text}

Provide relevant cultural context, medical information, or language nuances.
"""
            rag_service = RAGService(room.rag_collection)
            rag_results = rag_service.query(rag_query, top_k=3)

            if rag_results:
                return "\n\n".join([f"Context from {r['name']}: {r['content'][:300]}" for r in rag_results[:2]])

        except Exception as e:
            logger.error(f"RAG context query failed: {e}", exc_info=True)

        return None

    def _process_audio(self, message, audio_data, original_lang, target_lang, history, rag_context):
        """Process audio data for a message. Uses Celery if available."""
        try:
            audio_bytes = base64.b64decode(audio_data)
            logger.info(f"Received audio: {len(audio_bytes)} bytes")

            if len(audio_bytes) < 500:
                message.delete()
                return Response(
                    {"error": "Audio recording is too short or empty."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            audio_file = ContentFile(audio_bytes, name=f"audio_{message.id}.webm")
            message.audio_file = audio_file
            message.save()

            if not message.original_text or message.original_text == "[Voice Message]":
                # Try async processing with Celery if available
                if CELERY_ENABLED:
                    try:
                        from api.tasks.audio_tasks import transcribe_audio_async

                        # Queue async transcription - will also trigger translation
                        transcribe_audio_async.delay(
                            message_id=message.id,
                            audio_data=audio_bytes,
                            source_lang=original_lang,
                        )
                        logger.info(f"Audio transcription queued for message {message.id}")
                        # Return None to indicate async processing started
                        # Message will be updated by Celery task
                        message.original_text = "[Processing audio...]"
                        message.translated_text = "[Processing...]"
                        message.save()
                        return None
                    except Exception as e:
                        logger.warning(f"Celery task failed, falling back to sync: {e}")
                        # Fall through to synchronous processing

                # Synchronous processing (fallback or when Celery not available)
                transcriber = get_transcription_service()
                result = transcriber.transcribe(audio_bytes, source_lang=original_lang)

                if result["success"]:
                    transcription = result["transcription"]
                    if not transcription or len(transcription.strip()) == 0:
                        message.delete()
                        return Response(
                            {"error": "No speech detected in audio."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    message.audio_transcription = transcription
                    message.original_text = transcription

                    translator = get_translation_service()
                    translated_text = translator.translate_with_context(
                        text=transcription,
                        source_lang=original_lang,
                        target_lang=target_lang,
                        conversation_history=history,
                        sender_type=message.sender_type,
                        rag_context=rag_context,
                    )
                    message.translated_text = translated_text
                    message.save()
                else:
                    message.delete()
                    return Response(
                        {"error": f"Audio transcription failed: {result.get('error')}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            message.delete()
            return Response(
                {"error": f"Audio processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return None

    def _process_image(self, message, image_data, target_lang):
        """Process image data for a message."""
        try:
            image_bytes = base64.b64decode(image_data)
            # Use Gemini for image analysis (Ollama doesn't support this well)
            from api.services.gemini_service import get_gemini_service

            gemini = get_gemini_service()
            result = gemini.analyze_image(image_bytes, target_lang)
            message.image_description = result.get("description")
            message.save()
        except Exception:
            pass

    @action(detail=True, methods=["post"])
    def add_patient_context(self, request, pk=None):
        """Add patient context document to the RAG collection."""
        room = self.get_object()

        collection_id = request.data.get("collection_id")
        if collection_id:
            try:
                collection = Collection.objects.get(id=collection_id)
                room.rag_collection = collection
                room.save()
            except Collection.DoesNotExist:
                return Response(
                    {"error": f"Collection with id {collection_id} not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        elif not room.rag_collection:
            return Response(
                {"error": "No RAG collection configured. Please provide collection_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        patient_name = request.data.get("patient_name", room.patient_name or "Unknown Patient")
        cultural_background = request.data.get("cultural_background", "")
        medical_history = request.data.get("medical_history", "")
        language_notes = request.data.get("language_notes", "")

        document_content = f"""
PATIENT PROFILE: {patient_name}

CULTURAL BACKGROUND:
{cultural_background}

MEDICAL HISTORY:
{medical_history}

LANGUAGE & COMMUNICATION NOTES:
{language_notes}

PRIMARY LANGUAGE: {room.patient_language}
DOCTOR LANGUAGE: {room.doctor_language}
CHAT ROOM: {room.name}
"""

        try:
            rag_service = RAGService(room.rag_collection)
            item = rag_service.add_document(
                name=f"Patient Profile: {patient_name}",
                content=document_content,
                description=f"Comprehensive profile for {patient_name}",
                metadata={
                    "type": "patient_profile",
                    "patient_name": patient_name,
                    "chat_room_id": room.id,
                },
            )

            if not room.patient_name:
                room.patient_name = patient_name
                room.save()

            return Response(
                {"status": "success", "message": "Patient context added", "document_id": item.id},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to add patient context: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def get_doctor_assistance(self, request, pk=None):
        """Get AI-powered assistance for doctors. Uses Celery if available for async processing."""
        room = self.get_object()
        request_type = request.query_params.get("type", "general")
        async_mode = request.query_params.get("async", "false").lower() == "true"

        if not room.rag_collection:
            return Response(
                {"status": "no_collection", "message": "No RAG collection configured", "suggestions": []},
                status=status.HTTP_200_OK,
            )

        # Async mode - queue task and return immediately
        if async_mode and CELERY_ENABLED:
            try:
                from api.tasks.assistance_tasks import generate_doctor_assistance_async

                task = generate_doctor_assistance_async.delay(room_id=room.id, request_type=request_type)
                return Response(
                    {
                        "status": "processing",
                        "message": "Assistance is being generated",
                        "task_id": task.id,
                    },
                    status=status.HTTP_202_ACCEPTED,
                )
            except Exception as e:
                logger.warning(f"Celery task failed, falling back to sync: {e}")
                # Fall through to synchronous processing

        # Synchronous processing
        recent_messages = room.messages.order_by("-created_at")[:10]
        conversation_context = "\n".join(
            [f"{msg.sender_type}: {msg.original_text}" for msg in reversed(list(recent_messages))]
        )

        assistance_query = f"""
Based on this medical conversation, provide assistance to the doctor:

Patient Language: {room.patient_language}
Doctor Language: {room.doctor_language}

Recent Conversation:
{conversation_context}

Please suggest:
1. Important follow-up questions considering cultural context
2. Potential communication barriers to clarify
3. Cultural sensitivities to be aware of
4. Relevant medical information from patient history
"""

        try:
            rag_service = RAGService(room.rag_collection)
            result = rag_service.query_and_answer(assistance_query, top_k=5)

            if result["status"] == "success":
                return Response(
                    {"status": "success", "assistance": result["answer"], "sources": result.get("sources", [])},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"status": "error", "message": result.get("message", "Failed to generate assistance")},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing chat messages (read-only)."""

    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        room_id = self.request.query_params.get("room_id")
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        return queryset
