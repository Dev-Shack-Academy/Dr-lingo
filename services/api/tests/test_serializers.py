import pytest
from api.serializers.chat import ChatMessageSerializer, ChatRoomSerializer
from api.serializers.rag import CollectionItemSerializer, CollectionSerializer
from api.serializers.user import UserCreateSerializer, UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserSerializers:
    def test_user_serializer(self, doctor_user):
        serializer = UserSerializer(instance=doctor_user)
        assert serializer.data["username"] == doctor_user.username
        assert serializer.data["role"] == "doctor"

    def test_register_serializer_validation(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123!",
            "password_confirm": "password123!",
            "role": "patient",
            "first_name": "New",
            "last_name": "User",
        }
        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid() is True

    def test_register_serializer_mismatch_password(self):
        data = {
            "username": "mismatchuser",
            "email": "mismatch@example.com",
            "password": "password123!",
            "password_confirm": "mismatch",
            "role": "patient",
        }
        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid() is False
        assert "password" in serializer.errors


@pytest.mark.django_db
class TestChatSerializers:
    def test_chatroom_serializer(self, db):
        from api.models.chat import ChatRoom

        room = ChatRoom.objects.create(name="Test Room", patient_language="en", doctor_language="sw")
        serializer = ChatRoomSerializer(instance=room)
        assert serializer.data["name"] == "Test Room"
        assert serializer.data["patient_language"] == "en"

    def test_chatmessage_serializer(self, db):
        from api.models.chat import ChatMessage, ChatRoom

        room = ChatRoom.objects.create(name="Test Room")
        message = ChatMessage.objects.create(
            room=room, sender_type="patient", original_text="Hello", original_language="en"
        )
        serializer = ChatMessageSerializer(instance=message)
        assert serializer.data["original_text"] == "Hello"
        assert serializer.data["sender_type"] == "patient"


@pytest.mark.django_db
class TestRAGSerializers:
    def test_collection_serializer(self, db):
        from api.models.rag import Collection

        collection = Collection.objects.create(name="KB", description="Knowledge Base")
        serializer = CollectionSerializer(instance=collection)
        assert serializer.data["name"] == "KB"

    def test_collection_item_serializer(self, db):
        from api.models.rag import Collection, CollectionItem

        col = Collection.objects.create(name="KB")
        item = CollectionItem.objects.create(collection=col, name="Item", content="Content")
        serializer = CollectionItemSerializer(instance=item)
        assert serializer.data["name"] == "Item"
        assert serializer.data["content"] == "Content"
