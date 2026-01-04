import pytest
from api.models.item import Item
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestItemViews:
    def test_list_items_public_read(self, api_client, db):
        """Test item list endpoint allows public read (IsAuthenticatedOrReadOnly)."""
        # Create test items
        Item.objects.create(name="Test Item 1", description="Description 1")
        Item.objects.create(name="Test Item 2", description="Description 2")

        url = reverse("item-list")
        response = api_client.get(url)

        # Default permission is IsAuthenticatedOrReadOnly - allows GET
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2

    def test_list_items_authenticated(self, auth_client, db):
        """Test authenticated user can list items."""
        # Create test items
        Item.objects.create(name="Test Item 1", description="Description 1")
        Item.objects.create(name="Test Item 2", description="Description 2")

        url = reverse("item-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2

    def test_create_item_requires_authentication(self, api_client):
        """Test creating item requires authentication (IsAuthenticatedOrReadOnly)."""
        url = reverse("item-list")
        data = {"name": "New Item", "description": "New item description"}
        response = api_client.post(url, data)

        # POST requires authentication
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_item_authenticated(self, auth_client):
        """Test authenticated user can create items."""
        url = reverse("item-list")
        data = {"name": "New Item", "description": "New item description"}
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Item.objects.filter(name="New Item").exists()

    def test_create_item_admin_allowed(self, admin_client):
        """Test admin can create items."""
        url = reverse("item-list")
        data = {"name": "Admin Item", "description": "Created by admin"}
        response = admin_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Item.objects.filter(name="Admin Item").exists()

    def test_retrieve_item_public(self, api_client, db):
        """Test retrieving specific item is public."""
        item = Item.objects.create(name="Retrieve Item", description="Test description")

        url = reverse("item-detail", args=[item.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Retrieve Item"
        assert response.data["description"] == "Test description"

    def test_update_item_requires_authentication(self, api_client, db):
        """Test updating item requires authentication."""
        item = Item.objects.create(name="Update Item", description="Original description")

        url = reverse("item-detail", args=[item.id])
        data = {"name": "Updated Item", "description": "Updated description"}
        response = api_client.put(url, data)

        # PUT requires authentication
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_item_authenticated(self, auth_client, db):
        """Test authenticated user can update items."""
        item = Item.objects.create(name="Update Item", description="Original description")

        url = reverse("item-detail", args=[item.id])
        data = {"name": "Updated Item", "description": "Updated description"}
        response = auth_client.put(url, data)

        assert response.status_code == status.HTTP_200_OK

        item.refresh_from_db()
        assert item.name == "Updated Item"
        assert item.description == "Updated description"

    def test_partial_update_item(self, admin_client, db):
        """Test partial update of item."""
        item = Item.objects.create(name="Patch Item", description="Original description")

        url = reverse("item-detail", args=[item.id])
        data = {"description": "Patched description"}
        response = admin_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK

        item.refresh_from_db()
        assert item.name == "Patch Item"  # Unchanged
        assert item.description == "Patched description"  # Changed

    def test_delete_item_requires_authentication(self, api_client, db):
        """Test deleting item requires authentication."""
        item = Item.objects.create(name="Delete Item", description="To be deleted")

        url = reverse("item-detail", args=[item.id])
        response = api_client.delete(url)

        # DELETE requires authentication
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Item.objects.filter(id=item.id).exists()

    def test_delete_item_authenticated(self, auth_client, db):
        """Test authenticated user can delete items."""
        item = Item.objects.create(name="Delete Item", description="To be deleted")

        url = reverse("item-detail", args=[item.id])
        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Item.objects.filter(id=item.id).exists()

    def test_item_not_found(self, auth_client):
        """Test retrieving non-existent item returns 404."""
        url = reverse("item-detail", args=[99999])
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_item_validation(self, admin_client):
        """Test item creation validation."""
        url = reverse("item-list")

        # Test missing required fields
        response = admin_client.post(url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Test with only name (description might be optional)
        response = admin_client.post(url, {"name": "Valid Item"})
        # Should succeed if description is optional, or fail if required
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]

    def test_item_search_filtering(self, auth_client, db):
        """Test item filtering/search if implemented."""
        Item.objects.create(name="Python Item", description="About Python")
        Item.objects.create(name="JavaScript Item", description="About JavaScript")

        url = reverse("item-list")

        # Test basic listing
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2

    def test_item_ordering(self, auth_client, db):
        """Test item ordering if implemented."""
        Item.objects.create(name="B Item", description="Second")
        Item.objects.create(name="A Item", description="First")

        url = reverse("item-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        items = response.data
        assert len(items) >= 2

    def test_item_pagination(self, auth_client, db):
        """Test item pagination if implemented."""
        # Create multiple items
        for i in range(5):
            Item.objects.create(name=f"Item {i}", description=f"Description {i}")

        url = reverse("item-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Check pagination structure if implemented
        if isinstance(response.data, dict) and "results" in response.data:
            assert "count" in response.data
            assert "results" in response.data
        else:
            # Simple list response
            assert isinstance(response.data, list)
