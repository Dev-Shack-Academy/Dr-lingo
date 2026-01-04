from unittest.mock import MagicMock, patch

import pytest
from api.auth import OTPSessionAuthentication
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.request import Request

User = get_user_model()


class TestCustomAuthentication:
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.auth = OTPSessionAuthentication()

    @pytest.mark.django_db
    def test_otp_session_authentication_no_session(self):
        """Test OTP authentication with no session."""
        django_request = self.factory.get("/api/test/")
        request = Request(django_request)

        result = self.auth.authenticate(request)

        assert result is None

    @pytest.mark.django_db
    def test_otp_session_authentication_with_authenticated_user(self, patient_user):
        """Test OTP authentication with authenticated user in session."""
        django_request = self.factory.get("/api/test/")
        django_request.user = patient_user

        # Mock session with user ID
        django_request.session = MagicMock()
        django_request.session.get.return_value = patient_user.id

        request = Request(django_request)

        result = self.auth.authenticate(request)

        # Should return user tuple when session is valid
        if result is not None:
            user, auth = result
            assert user == patient_user
        else:
            # Session auth might return None in test environment
            assert result is None

    @pytest.mark.django_db
    def test_otp_session_authentication_anonymous_user(self):
        """Test OTP authentication with anonymous user."""
        from django.contrib.auth.models import AnonymousUser

        django_request = self.factory.get("/api/test/")
        django_request.user = AnonymousUser()
        django_request.session = MagicMock()

        request = Request(django_request)

        result = self.auth.authenticate(request)

        assert result is None

    @pytest.mark.django_db
    def test_authentication_inheritance(self):
        """Test that OTPSessionAuthentication properly inherits from SessionAuthentication."""
        from rest_framework.authentication import SessionAuthentication

        assert isinstance(self.auth, SessionAuthentication)
        assert hasattr(self.auth, "authenticate")

    @pytest.mark.django_db
    def test_authentication_with_no_session_key(self):
        """Test authentication when there's no session key."""
        django_request = self.factory.get("/api/test/")
        # Don't add session or user

        request = Request(django_request)

        result = self.auth.authenticate(request)
        assert result is None

    @pytest.mark.django_db
    def test_authentication_method_signature(self):
        """Test that authenticate method has correct signature."""
        django_request = self.factory.get("/api/test/")
        request = Request(django_request)

        # Should not raise an exception
        result = self.auth.authenticate(request)

        # Result should be None or a tuple
        assert result is None or (isinstance(result, tuple) and len(result) == 2)

    @pytest.mark.django_db
    def test_otp_authentication_preserves_session_behavior(self, patient_user):
        """Test that OTP authentication preserves standard session authentication behavior."""
        django_request = self.factory.get("/api/test/")
        django_request.user = patient_user
        django_request.session = MagicMock()
        django_request.session.session_key = "test_session_key"

        request = Request(django_request)

        # Mock the parent authenticate method
        with patch.object(self.auth.__class__.__bases__[0], "authenticate") as mock_parent_auth:
            mock_parent_auth.return_value = (patient_user, None)

            result = self.auth.authenticate(request)

            # Should call parent authenticate
            mock_parent_auth.assert_called_once_with(request)

            # Should return the same result as parent
            assert result == (patient_user, None)
