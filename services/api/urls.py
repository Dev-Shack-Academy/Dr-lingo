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
    confirm_otp_setup,
    health_check,
    login,
    logout,
    me,
    register,
    setup_otp,
    task_status,
    update_profile,
    verify_otp,
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
    # Authentication endpoints (session-based with OTP)
    path("auth/register/", register, name="auth-register"),
    path("auth/login/", login, name="auth-login"),
    path("auth/logout/", logout, name="auth-logout"),
    path("auth/me/", me, name="auth-me"),
    path("auth/profile/", update_profile, name="auth-profile"),
    path("auth/change-password/", change_password, name="auth-change-password"),
    # OTP endpoints
    path("auth/verify-otp/", verify_otp, name="auth-verify-otp"),
    path("auth/setup-otp/", setup_otp, name="auth-setup-otp"),
    path("auth/confirm-otp-setup/", confirm_otp_setup, name="auth-confirm-otp-setup"),
]
