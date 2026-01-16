"""
WebSocket URL routing for Django Channels.

This module defines the WebSocket URL patterns for real-time chat functionality.
"""

from django.urls import re_path

from api.consumers import ChatConsumer

websocket_urlpatterns = [
    # Chat room WebSocket endpoint
    # ws://host/ws/chat/{room_id}/
    re_path(r"ws/chat/(?P<room_id>\d+)/$", ChatConsumer.as_asgi()),
]
