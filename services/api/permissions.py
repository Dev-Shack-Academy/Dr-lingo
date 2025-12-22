from rest_framework.permissions import BasePermission


class IsPatient(BasePermission):
    """Allow access only to patients."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == "patient"


class IsDoctor(BasePermission):
    """Allow access only to doctors."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == "doctor"


class IsAdmin(BasePermission):
    """Allow access only to admins."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.role == "admin" or request.user.is_superuser)
        )


class IsDoctorOrAdmin(BasePermission):
    """Allow access to doctors and admins."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ["doctor", "admin"] or request.user.is_superuser


class CanAccessRAG(BasePermission):
    """Allow access to RAG features (doctors and admins only)."""

    message = "RAG access is restricted to doctors and administrators."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, "can_access_rag") and request.user.can_access_rag()


class CanViewPatientContext(BasePermission):
    """Allow viewing patient context (doctors and admins only)."""

    message = "Patient context access is restricted to medical staff."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, "can_view_patient_context") and request.user.can_view_patient_context()


class CanGetAIAssistance(BasePermission):
    """Allow AI assistance requests (doctors and admins only)."""

    message = "AI assistance is restricted to medical staff."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, "can_get_ai_assistance") and request.user.can_get_ai_assistance()


class IsRoomParticipant(BasePermission):
    """Allow access only to participants of a chat room."""

    message = "You are not a participant in this chat room."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins can access all rooms
        if request.user.role == "admin" or request.user.is_superuser:
            return True

        # Check if user is a participant
        # This assumes ChatRoom has a participants field or similar
        if hasattr(obj, "participants"):
            return request.user in obj.participants.all()

        # For now, allow authenticated users
        return True


class ReadOnly(BasePermission):
    """Allow read-only access."""

    def has_permission(self, request, view):
        return request.method in ["GET", "HEAD", "OPTIONS"]


# Composite permissions
class IsAuthenticatedOrReadOnly(BasePermission):
    """Allow authenticated users full access, others read-only."""

    def has_permission(self, request, view):
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        return request.user and request.user.is_authenticated
