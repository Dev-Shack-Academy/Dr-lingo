import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestInfrastructure:
    def test_admin_permission_denied_for_doctor(self, auth_client):
        # Using UserViewSet which requires IsAdmin
        url = reverse("user-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_permission_allowed_for_admin(self, admin_client):
        url = reverse("user-list")
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_health_check_public(self, api_client):
        url = reverse("health-check")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ok"

    def test_celery_status_authenticated_only(self, api_client, admin_client):
        url = reverse("celery-status")
        # Anonymous
        response = api_client.get(url)
        print(
            f"DEBUG: url={url}, status={response.status_code}, content={response.data if hasattr(response, 'data') else ''}"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        # Authenticated
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
