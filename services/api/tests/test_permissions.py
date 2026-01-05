from unittest.mock import MagicMock

from api.permissions import (
    CanAccessRAG,
    CanGetAIAssistance,
    CanViewPatientContext,
    IsAdmin,
    IsDoctor,
    IsDoctorOrAdmin,
    IsPatient,
)
from rest_framework.test import APIRequestFactory


class TestPermissions:
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = APIRequestFactory()
        self.view = MagicMock()

    def test_is_patient_permission(self, patient_user, doctor_user):
        """Test IsPatient permission class."""
        permission = IsPatient()
        request = self.factory.get("/")

        # Patient should have permission
        request.user = patient_user
        assert permission.has_permission(request, self.view) is True

        # Doctor should not have permission
        request.user = doctor_user
        assert permission.has_permission(request, self.view) is False

    def test_is_doctor_permission(self, patient_user, doctor_user):
        """Test IsDoctor permission class."""
        permission = IsDoctor()
        request = self.factory.get("/")

        # Doctor should have permission
        request.user = doctor_user
        assert permission.has_permission(request, self.view) is True

        # Patient should not have permission
        request.user = patient_user
        assert permission.has_permission(request, self.view) is False

    def test_is_admin_permission(self, doctor_user, admin_user):
        """Test IsAdmin permission class."""
        permission = IsAdmin()
        request = self.factory.get("/")

        # Admin should have permission
        request.user = admin_user
        assert permission.has_permission(request, self.view) is True

        # Doctor should not have permission
        request.user = doctor_user
        assert permission.has_permission(request, self.view) is False

    def test_is_doctor_or_admin_permission(self, patient_user, doctor_user, admin_user):
        """Test IsDoctorOrAdmin permission class."""
        permission = IsDoctorOrAdmin()
        request = self.factory.get("/")

        # Doctor should have permission
        request.user = doctor_user
        assert permission.has_permission(request, self.view) is True

        # Admin should have permission
        request.user = admin_user
        assert permission.has_permission(request, self.view) is True

        # Patient should not have permission
        request.user = patient_user
        assert permission.has_permission(request, self.view) is False

    def test_can_access_rag_permission(self, patient_user, doctor_user, admin_user):
        """Test CanAccessRAG permission class."""
        permission = CanAccessRAG()
        request = self.factory.get("/")

        # Doctor should have permission
        request.user = doctor_user
        assert permission.has_permission(request, self.view) is True

        # Admin should have permission
        request.user = admin_user
        assert permission.has_permission(request, self.view) is True

        # Patient should not have permission
        request.user = patient_user
        assert permission.has_permission(request, self.view) is False

    def test_can_view_patient_context_permission(self, patient_user, doctor_user, admin_user):
        """Test CanViewPatientContext permission class."""
        permission = CanViewPatientContext()
        request = self.factory.get("/")

        # Doctor should have permission
        request.user = doctor_user
        assert permission.has_permission(request, self.view) is True

        # Admin should have permission
        request.user = admin_user
        assert permission.has_permission(request, self.view) is True

        # Patient should not have permission
        request.user = patient_user
        assert permission.has_permission(request, self.view) is False

    def test_can_get_ai_assistance_permission(self, patient_user, doctor_user, admin_user):
        """Test CanGetAIAssistance permission class."""
        permission = CanGetAIAssistance()
        request = self.factory.get("/")

        # Doctor should have permission
        request.user = doctor_user
        assert permission.has_permission(request, self.view) is True

        # Admin should have permission
        request.user = admin_user
        assert permission.has_permission(request, self.view) is True

        # Patient should not have permission
        request.user = patient_user
        assert permission.has_permission(request, self.view) is False

    def test_unauthenticated_user_permissions(self):
        """Test permissions with unauthenticated user."""
        from django.contrib.auth.models import AnonymousUser

        permissions = [
            IsPatient(),
            IsDoctor(),
            IsAdmin(),
            IsDoctorOrAdmin(),
            CanAccessRAG(),
            CanViewPatientContext(),
            CanGetAIAssistance(),
        ]

        request = self.factory.get("/")
        request.user = AnonymousUser()

        # All permissions should deny anonymous users
        for permission in permissions:
            assert permission.has_permission(request, self.view) is False

    def test_permission_messages(self):
        """Test permission denial messages."""
        permission = IsDoctor()

        # Check that permission has appropriate message
        assert hasattr(permission, "message"), "IsDoctor permission should have a message attribute"

        # Test with actual permission check
        request = self.factory.get("/")
        request.user = MagicMock()
        request.user.is_authenticated = True
        request.user.role = "patient"

        result = permission.has_permission(request, self.view)
        assert result is False
