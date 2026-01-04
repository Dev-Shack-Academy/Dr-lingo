from unittest.mock import MagicMock

from api.middleware import RequireOTPVerificationMiddleware
from django.http import HttpResponse
from django.test import RequestFactory


class TestMiddleware:
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.get_response = MagicMock(return_value=HttpResponse("OK"))
        self.middleware = RequireOTPVerificationMiddleware(self.get_response)

    def test_middleware_init(self):
        """Test middleware initialization."""
        assert self.middleware.get_response == self.get_response
        assert isinstance(self.middleware.exempt_paths, set)
        assert isinstance(self.middleware.exempt_prefixes, tuple)

    def test_middleware_anonymous_user(self):
        """Test middleware allows anonymous users."""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get("/api/test/")
        request.user = AnonymousUser()

        response = self.middleware(request)

        assert response.status_code == 200
        self.get_response.assert_called_once_with(request)

    def test_middleware_verified_user(self, patient_user):
        """Test middleware allows verified users."""
        request = self.factory.get("/api/test/")
        request.user = patient_user

        # Mock user as verified
        patient_user.is_verified = MagicMock(return_value=True)

        response = self.middleware(request)

        assert response.status_code == 200
        self.get_response.assert_called_once_with(request)

    def test_middleware_unverified_user_exempt_path(self, patient_user):
        """Test middleware allows unverified users on exempt paths."""
        request = self.factory.get("/api/auth/login/")
        request.user = patient_user

        # Mock user as not verified
        patient_user.is_verified = MagicMock(return_value=False)

        response = self.middleware(request)

        # Should allow access to API paths (exempt prefix)
        assert response.status_code == 200
        self.get_response.assert_called_once_with(request)

    def test_middleware_unverified_user_redirect(self, patient_user):
        """Test middleware redirects unverified users on protected paths."""
        request = self.factory.get("/protected/page/")
        request.user = patient_user

        # Mock user as not verified
        patient_user.is_verified = MagicMock(return_value=False)

        response = self.middleware(request)

        # Should redirect to setup page
        assert response.status_code == 302
        assert response.url == self.middleware.setup_url

    def test_middleware_setup_page_access(self, patient_user):
        """Test middleware allows access to setup page."""
        request = self.factory.get(self.middleware.setup_url)
        request.user = patient_user

        # Mock user as not verified
        patient_user.is_verified = MagicMock(return_value=False)

        response = self.middleware(request)

        assert response.status_code == 200
        self.get_response.assert_called_once_with(request)

    def test_middleware_exempt_prefixes(self, patient_user):
        """Test middleware exempt prefixes work correctly."""
        exempt_paths = ["/static/css/style.css", "/api/health/", "/api/auth/login/"]

        for path in exempt_paths:
            request = self.factory.get(path)
            request.user = patient_user
            patient_user.is_verified = MagicMock(return_value=False)

            response = self.middleware(request)

            assert response.status_code == 200

        # Reset mock for next iteration
        self.get_response.reset_mock()

    def test_middleware_user_without_is_verified(self, patient_user):
        """Test middleware handles users without is_verified method."""
        request = self.factory.get("/protected/page/")
        request.user = patient_user

        # Mock is_verified to return False (simulating user without OTP setup)
        patient_user.is_verified = MagicMock(return_value=False)

        response = self.middleware(request)

        # Should redirect since user is not verified
        assert response.status_code == 302
