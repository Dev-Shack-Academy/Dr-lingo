from rest_framework import viewsets

from api.models import Item
from api.serializers import ItemSerializer


class ItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Item CRUD operations.

    ModelViewSet automatically provides:
    - list(): GET /api/items/ - List all items
    - create(): POST /api/items/ - Create a new item
    - retrieve(): GET /api/items/:id/ - Get a specific item
    - update(): PUT /api/items/:id/ - Update an item
    - partial_update(): PATCH /api/items/:id/ - Partially update an item
    - destroy(): DELETE /api/items/:id/ - Delete an item
    """

    queryset = Item.objects.all()
    serializer_class = ItemSerializer
