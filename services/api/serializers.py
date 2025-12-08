"""
Serializers convert complex data types (like Django models) to/from JSON.

Serializers handle:
- Converting model instances to JSON (serialization)
- Converting JSON to model instances (deserialization)
- Validation of incoming data
- Nested relationships
"""

from rest_framework import serializers

from .models import ChatMessage, ChatRoom, Item


class ItemSerializer(serializers.ModelSerializer):
    """
    Serializer for Item model.

    Automatically handles all CRUD operations for Item objects.
    The Meta class specifies which model and fields to include.
    """

    class Meta:
        model = Item
        fields = ["id", "name", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ChatMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for ChatMessage model with translation support.
    """

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
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "translated_text", "translated_language", "image_description"]


class ChatRoomSerializer(serializers.ModelSerializer):
    """
    Serializer for ChatRoom model.
    """

    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "name",
            "room_type",
            "patient_language",
            "doctor_language",
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
    """
    Lightweight serializer for listing chat rooms (without messages).
    """

    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "name",
            "room_type",
            "patient_language",
            "doctor_language",
            "created_at",
            "updated_at",
            "is_active",
            "message_count",
            "last_message",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

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
