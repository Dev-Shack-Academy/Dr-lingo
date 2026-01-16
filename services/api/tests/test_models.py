import pytest
from api.models.chat import ChatMessage, ChatRoom
from api.models.rag import Collection, CollectionItem
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(username="testuser", password="password123", role="doctor")
        assert user.username == "testuser"
        assert user.role == "doctor"
        assert str(user) == "testuser (Doctor)"

    def test_user_roles(self, patient_user, doctor_user, admin_user):
        assert patient_user.is_patient is True
        assert doctor_user.is_doctor is True
        assert admin_user.is_admin_user is True

    def test_user_permissions(self, patient_user, doctor_user):
        assert patient_user.can_access_rag() is False
        assert doctor_user.can_access_rag() is True
        assert doctor_user.can_view_patient_context() is True
        assert doctor_user.can_get_ai_assistance() is True


@pytest.mark.django_db
class TestChatModels:
    def test_create_chatroom(self):
        room = ChatRoom.objects.create(name="Emergency Room", patient_language="sw", doctor_language="en")
        assert room.name == "Emergency Room"
        assert str(room) == "Emergency Room (sw <-> en)"

    def test_create_message(self, db):
        room = ChatRoom.objects.create(name="Test Room")
        message = ChatMessage.objects.create(
            room=room, sender_type="doctor", original_text="Hello", original_language="en"
        )
        assert message.room == room
        assert message.sender_type == "doctor"
        assert str(message).startswith("doctor - Hello")


@pytest.mark.django_db
class TestRAGModels:
    def test_create_collection(self):
        collection = Collection.objects.create(
            name="Medical Protocols", description="Emergency protocols", collection_type="knowledge_base"
        )
        assert collection.name == "Medical Protocols"
        assert str(collection) == "Medical Protocols"

    def test_create_collection_item(self, db):
        collection = Collection.objects.create(name="Test Collection")
        item = CollectionItem.objects.create(
            collection=collection, name="Document 1", content="Important medical info"
        )
        assert item.collection == collection
        assert item.name == "Document 1"
        assert str(item) == "Document 1 - Test Collection"
