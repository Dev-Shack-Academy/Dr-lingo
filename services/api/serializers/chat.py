from rest_framework import serializers

from api.models import ChatMessage, ChatRoom


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for ChatMessage model with translation support."""

    audio_url = serializers.SerializerMethodField()
    tts_audio_url = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "room",
            "sender_type",
            "original_text",
            "original_language",
            "translated_text",
            "translated_language",
            "has_image",
            "image_url",
            "image_description",
            "has_audio",
            "audio_url",
            "audio_duration",
            "audio_transcription",
            "tts_audio_url",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "translated_text",
            "translated_language",
            "image_description",
            "audio_url",
            "audio_transcription",
            "tts_audio_url",
        ]

    def get_audio_url(self, obj):
        if obj.audio_file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.audio_file.url)
            return obj.audio_file.url
        return None

    def get_tts_audio_url(self, obj):
        if obj.tts_audio:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.tts_audio.url)
            return obj.tts_audio.url
        return None


class ChatRoomSerializer(serializers.ModelSerializer):
    """Serializer for ChatRoom model."""

    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    rag_collection_name = serializers.CharField(source="rag_collection.name", read_only=True)

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "name",
            "room_type",
            "patient_language",
            "doctor_language",
            "patient_name",
            "rag_collection",
            "rag_collection_name",
            "created_at",
            "updated_at",
            "is_active",
            "messages",
            "message_count",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_message_count(self, obj):
        return obj.messages.count()


class ChatRoomListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing chat rooms (without messages)."""

    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    rag_collection_name = serializers.CharField(source="rag_collection.name", read_only=True)
    has_rag = serializers.SerializerMethodField()
    patient_context = serializers.SerializerMethodField()
    linked_knowledge_bases = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "name",
            "room_type",
            "patient_language",
            "doctor_language",
            "patient_name",
            "rag_collection",
            "rag_collection_name",
            "has_rag",
            "patient_context",
            "linked_knowledge_bases",
            "created_at",
            "updated_at",
            "is_active",
            "message_count",
            "last_message",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_has_rag(self, obj):
        return obj.rag_collection is not None

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                "text": last_msg.original_text[:100],
                "sender": last_msg.sender_type,
                "created_at": last_msg.created_at,
            }
        return None

    def get_patient_context(self, obj):
        """Get patient context details (documents) for doctors/admins."""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        # Only show to doctors and admins
        if request.user.role not in ["doctor", "admin"] and not request.user.is_superuser:
            return None

        # Get patient context collection linked to this room
        patient_contexts = obj.patient_contexts.filter(collection_type="patient_context")
        if not patient_contexts.exists():
            return None

        context_data = []
        for pc in patient_contexts:
            items = pc.items.all()[:10]  # Limit to 10 items
            context_data.append(
                {
                    "id": pc.id,
                    "name": pc.name,
                    "description": pc.description,
                    "items": [
                        {
                            "id": item.id,
                            "name": item.name,
                            "content": item.content[:200] + "..." if len(item.content) > 200 else item.content,
                            "metadata": item.metadata,
                        }
                        for item in items
                    ],
                }
            )
        return context_data

    def get_linked_knowledge_bases(self, obj):
        """Get knowledge bases linked to patient contexts for this room."""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        # Only show to doctors and admins
        if request.user.role not in ["doctor", "admin"] and not request.user.is_superuser:
            return None

        # Get all knowledge bases linked to patient contexts for this room
        patient_contexts = obj.patient_contexts.filter(collection_type="patient_context")
        knowledge_bases = set()

        for pc in patient_contexts:
            for kb in pc.knowledge_bases.all():
                knowledge_bases.add((kb.id, kb.name, kb.description, kb.items.count()))

        return [{"id": kb[0], "name": kb[1], "description": kb[2], "items_count": kb[3]} for kb in knowledge_bases]
