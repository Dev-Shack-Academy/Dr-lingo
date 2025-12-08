"""
API views (endpoints) for handling HTTP requests.

ViewSets provide the logic for handling CRUD operations:
- List all items (GET /api/items/)
- Create new item (POST /api/items/)
- Retrieve single item (GET /api/items/:id/)
- Update item (PUT /api/items/:id/)
- Delete item (DELETE /api/items/:id/)

Example: ItemViewSet demonstrates the standard pattern for API endpoints.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .gemini_service import get_gemini_service
from .models import ChatMessage, ChatRoom, Item
from .serializers import ChatMessageSerializer, ChatRoomListSerializer, ChatRoomSerializer, ItemSerializer


class ItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Item CRUD operations.

    ModelViewSet automatically provides:
    - list(): GET /api/items/ - List all items
    - create(): POST /api/items/ - Create a new item
    - retrieve(): GET /api/items/:id/ - Get a specific item
    - update(): PUT /api/items/:id/ - Update an item
    - partial_update(): PATCH /api/items/:id/ - Partially update an item
    - destroy(): DELETE /api/items/:id/ - Delete an item

    To customize behavior, override these methods.
    """

    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class ChatRoomViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat rooms.
    """

    queryset = ChatRoom.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return ChatRoomListSerializer
        return ChatRoomSerializer

    @action(detail=True, methods=["post"])
    def send_message(self, request, pk=None):
        """
        Send a message in a chat room with automatic translation.

        POST /api/chat-rooms/{id}/send_message/
        Body: {
            "sender_type": "patient" or "doctor",
            "text": "message text",
            "image": "base64 image data (optional)"
        }
        """
        room = self.get_object()
        sender_type = request.data.get("sender_type")
        text = request.data.get("text")
        image_data = request.data.get("image")

        if not sender_type or not text:
            return Response({"error": "sender_type and text are required"}, status=status.HTTP_400_BAD_REQUEST)

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

        # Translate message
        try:
            gemini = get_gemini_service()
            translated_text = gemini.translate_with_context(
                text=text,
                source_lang=original_lang,
                target_lang=target_lang,
                conversation_history=history,
                sender_type=sender_type,
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
        )

        # Process image if provided
        if image_data:
            try:
                import base64

                image_bytes = base64.b64decode(image_data)
                result = gemini.analyze_image(image_bytes, target_lang)
                message.image_description = result.get("description")
                message.save()
            except Exception:
                # Image processing failed, but message is still saved
                pass

        serializer = ChatMessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChatMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing chat messages (read-only).
    Messages are created through ChatRoomViewSet.send_message action.
    """

    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        room_id = self.request.query_params.get("room_id")
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        return queryset


@api_view(["GET"])
def health_check(request):
    """
    Health check endpoint to verify the API is running.

    Returns:
        200 OK with a ping response
    """
    return Response({"status": "ok", "message": "pong"}, status=status.HTTP_200_OK)
