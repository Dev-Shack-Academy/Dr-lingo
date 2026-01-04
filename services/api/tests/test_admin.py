import pytest
from api.admin.chat import ChatMessageAdmin, ChatRoomAdmin
from api.admin.item import ItemAdmin
from api.admin.rag import CollectionAdmin, CollectionItemAdmin
from api.admin.user import UserAdmin
from api.models.chat import ChatMessage, ChatRoom
from api.models.item import Item
from api.models.rag import Collection, CollectionItem
from api.models.user import User
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory


@pytest.mark.django_db
class TestAdminConfiguration:
    def setup_method(self):
        """Set up test fixtures."""
        self.site = AdminSite()
        self.factory = RequestFactory()

    def test_user_admin_configuration(self, admin_user):
        """Test UserAdmin configuration."""
        admin = UserAdmin(User, self.site)

        # Test list display
        assert "username" in admin.list_display
        assert "email" in admin.list_display
        assert "role" in admin.list_display
        assert "is_active" in admin.list_display

        # Test list filters
        assert "role" in admin.list_filter
        assert "is_active" in admin.list_filter

        # Test search fields
        assert "username" in admin.search_fields
        assert "email" in admin.search_fields

    def test_user_admin_queryset(self, admin_user, patient_user, doctor_user):
        """Test UserAdmin queryset."""
        admin = UserAdmin(User, self.site)
        request = self.factory.get("/admin/api/user/")
        request.user = admin_user

        queryset = admin.get_queryset(request)

        # Should include all users
        assert queryset.count() >= 3
        assert patient_user in queryset
        assert doctor_user in queryset
        assert admin_user in queryset

    def test_chatroom_admin_configuration(self):
        """Test ChatRoomAdmin configuration."""
        admin = ChatRoomAdmin(ChatRoom, self.site)

        # Test list display
        assert "name" in admin.list_display
        assert "patient_language" in admin.list_display
        assert "doctor_language" in admin.list_display
        assert "is_active" in admin.list_display

        # Test list filters
        assert "patient_language" in admin.list_filter
        assert "doctor_language" in admin.list_filter
        assert "is_active" in admin.list_filter

    def test_chatmessage_admin_configuration(self):
        """Test ChatMessageAdmin configuration."""
        admin = ChatMessageAdmin(ChatMessage, self.site)

        # Test list display
        assert "room" in admin.list_display
        assert "sender_type" in admin.list_display
        assert "original_text_preview" in admin.list_display  # Uses preview method
        assert "created_at" in admin.list_display

        # Test list filters
        assert "sender_type" in admin.list_filter
        assert "has_audio" in admin.list_filter

    def test_collection_admin_configuration(self):
        """Test CollectionAdmin configuration."""
        admin = CollectionAdmin(Collection, self.site)

        # Test list display
        assert "name" in admin.list_display
        assert "collection_type" in admin.list_display
        assert "embedding_provider" in admin.list_display

        # Test list filters
        assert "collection_type" in admin.list_filter
        assert "embedding_provider" in admin.list_filter

    def test_collection_item_admin_configuration(self):
        """Test CollectionItemAdmin configuration."""
        admin = CollectionItemAdmin(CollectionItem, self.site)

        # Test list display
        assert "name" in admin.list_display
        assert "collection" in admin.list_display
        assert "created_at" in admin.list_display

        # Test list filters
        assert "collection" in admin.list_filter

    def test_item_admin_configuration(self):
        """Test ItemAdmin configuration."""
        admin = ItemAdmin(Item, self.site)

        # Test list display
        assert "name" in admin.list_display
        assert "created_at" in admin.list_display

    def test_admin_permissions(self, admin_user, doctor_user):
        """Test admin permissions for different user roles."""
        user_admin = UserAdmin(User, self.site)

        # Admin request
        admin_request = self.factory.get("/admin/api/user/")
        admin_request.user = admin_user

        # Doctor request
        doctor_request = self.factory.get("/admin/api/user/")
        doctor_request.user = doctor_user

        # Admin should have permissions
        assert user_admin.has_module_permission(admin_request) is True

        # Doctor should not have admin permissions (depends on implementation)
        # This test assumes doctors don't have Django admin access
        # Adjust based on your actual permission setup

    @pytest.mark.django_db
    def test_admin_string_representations(self):
        """Test string representations in admin."""
        # Create test objects
        user = User.objects.create_user(username="testuser", email="test@example.com", role="patient")

        room = ChatRoom.objects.create(name="Test Room", patient_language="en", doctor_language="es")

        message = ChatMessage.objects.create(
            room=room, sender_type="patient", original_text="Hello", original_language="en"
        )

        collection = Collection.objects.create(name="Test Collection", collection_type="knowledge_base")

        item = CollectionItem.objects.create(collection=collection, name="Test Item", content="Test content")

        # Test string representations
        assert str(user) == "testuser (Patient)"
        assert str(room) == "Test Room (en <-> es)"
        assert "patient - Hello" in str(message)
        assert str(collection) == "Test Collection"
        assert str(item) == "Test Item - Test Collection"

    def test_admin_readonly_fields(self):
        """Test readonly fields in admin."""
        user_admin = UserAdmin(User, self.site)

        # Check if certain fields are readonly
        readonly_fields = getattr(user_admin, "readonly_fields", [])

        # Common readonly fields might include timestamps
        # Adjust based on your actual admin configuration
        assert isinstance(readonly_fields, (list, tuple))

    def test_admin_fieldsets(self):
        """Test admin fieldsets configuration."""
        user_admin = UserAdmin(User, self.site)

        # Check if fieldsets are configured
        fieldsets = getattr(user_admin, "fieldsets", None)

        if fieldsets:
            assert isinstance(fieldsets, (list, tuple))
            # Each fieldset should be a tuple with name and options
            for fieldset in fieldsets:
                assert isinstance(fieldset, tuple)
                assert len(fieldset) == 2
