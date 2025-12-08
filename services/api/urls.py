"""
URL routing configuration for the API.

Maps URL patterns to views:
- /api/items/ -> ItemViewSet
- /api/chat-rooms/ -> ChatRoomViewSet
- /api/messages/ -> ChatMessageViewSet
- /api/health/ -> health_check

The router automatically creates standard REST endpoints for ViewSets.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ChatMessageViewSet, ChatRoomViewSet, ItemViewSet, health_check

# Create a router and register viewsets
router = DefaultRouter()
router.register(r"items", ItemViewSet, basename="item")
router.register(r"chat-rooms", ChatRoomViewSet, basename="chatroom")
router.register(r"messages", ChatMessageViewSet, basename="message")

urlpatterns = [
    path("", include(router.urls)),
    path("health/", health_check, name="health-check"),
]
