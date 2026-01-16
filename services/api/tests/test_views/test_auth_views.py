from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestAuthViews:
    def test_register_user(self, api_client):
        url = reverse("auth-register")
        data = {
            "username": "newpatient",
            "email": "patient@example.com",
            "password": "password123!",
            "password_confirm": "password123!",
            "role": "patient",
            "first_name": "New",
            "last_name": "Patient",
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username="newpatient").exists()

    def test_login_user(self, api_client, doctor_user):
        url = reverse("auth-login")
        data = {"username": doctor_user.username, "password": "password123"}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert "user" in response.data

    def test_me_endpoint(self, auth_client, doctor_user):
        url = reverse("auth-me")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == doctor_user.username

    def test_logout_user(self, auth_client):
        url = reverse("auth-logout")
        response = auth_client.post(url)
        assert response.status_code == status.HTTP_200_OK

    def test_unauthorized_me(self, api_client):
        url = reverse("auth-me")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch("django_otp.plugins.otp_totp.models.TOTPDevice.objects.create")
    @patch("qrcode.QRCode")
    def test_setup_otp(self, mock_qrcode, mock_device_create, auth_client):
        url = reverse("auth-setup-otp")
        mock_device = MagicMock()
        mock_device.config_url = "otpauth://totp/DrLingo:test?secret=base32secret"
        mock_device.key = "base32secret"
        mock_device_create.return_value = mock_device

        response = auth_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert "qr_code" in response.data
        assert "secret" in response.data

    @patch("django_otp.plugins.otp_totp.models.TOTPDevice.objects.filter")
    def test_confirm_otp_setup(self, mock_device_filter, auth_client):
        url = reverse("auth-confirm-otp-setup")
        mock_device = MagicMock()
        mock_device.verify_token.return_value = True
        mock_device.persistent_id = "test_device_id"  # Crucial for serialization
        mock_device_filter.return_value.first.return_value = mock_device

        data = {"otp_token": "123456"}
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("success") is True
        assert mock_device.save.called

    @patch("django_otp.devices_for_user")
    def test_verify_otp(self, mock_devices_for_user, auth_client):
        url = reverse("auth-verify-otp")
        mock_device = MagicMock()
        mock_device.verify_token.return_value = True
        mock_device.persistent_id = "test_device_id"  # Crucial for serialization
        mock_devices_for_user.return_value = [mock_device]

        data = {"otp_token": "123456"}
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"
