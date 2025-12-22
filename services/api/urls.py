from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    ChatMessageViewSet,
    ChatRoomViewSet,
    CollectionItemViewSet,
    CollectionViewSet,
    ItemViewSet,
    UserViewSet,
    celery_status,
    change_password,
    health_check,
    login,
    me,
    register,
    task_status,
    update_profile,
)

# Create a router and register viewsets
router = DefaultRouter()
router.register(r"items", ItemViewSet, basename="item")
router.register(r"chat-rooms", ChatRoomViewSet, basename="chatroom")
router.register(r"messages", ChatMessageViewSet, basename="message")
router.register(r"collections", CollectionViewSet, basename="collection")
router.register(r"collection-items", CollectionItemViewSet, basename="collectionitem")
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
    path("health/", health_check, name="health-check"),
    # Celery task status endpoints
    path("tasks/<str:task_id>/", task_status, name="task-status"),
    path("celery/status/", celery_status, name="celery-status"),
    # Authentication endpoints
    path("auth/register/", register, name="auth-register"),
    path("auth/login/", login, name="auth-login"),
    path("auth/me/", me, name="auth-me"),
    path("auth/profile/", update_profile, name="auth-profile"),
    path("auth/change-password/", change_password, name="auth-change-password"),
]

# JWT Token refresh endpoints (from simplejwt)
try:
    from rest_framework_simplejwt.views import TokenRefreshView

    urlpatterns.append(path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"))
except ImportError:
    pass
