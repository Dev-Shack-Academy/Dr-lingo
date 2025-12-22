import logging

from django.contrib.auth import authenticate, get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.serializers.user import (
    ChangePasswordSerializer,
    LoginSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

logger = logging.getLogger(__name__)
User = get_user_model()


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user.

    POST /api/auth/register/
    """
    serializer = UserCreateSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "status": "success",
                "message": "User registered successfully",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """
    Login and get JWT tokens.

    POST /api/auth/login/
    """
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    username = serializer.validated_data["username"]
    password = serializer.validated_data["password"]

    user = authenticate(username=username, password=password)
    if not user:
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return Response(
            {"error": "User account is disabled"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Generate tokens (requires djangorestframework-simplejwt)
    try:
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )
    except ImportError:
        # Fallback without JWT
        return Response(
            {
                "message": "Login successful",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """
    Get current user profile.

    GET /api/auth/me/
    """
    return Response(UserSerializer(request.user).data)


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update current user profile.

    PUT/PATCH /api/auth/profile/
    """
    serializer = UserUpdateSerializer(
        request.user,
        data=request.data,
        partial=request.method == "PATCH",
    )
    if serializer.is_valid():
        serializer.save()
        return Response(UserSerializer(request.user).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password.

    POST /api/auth/change-password/
    """
    serializer = ChangePasswordSerializer(
        data=request.data,
        context={"request": request},
    )
    if serializer.is_valid():
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"status": "success", "message": "Password changed successfully"})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management (admin only).
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        from api.permissions import IsAdmin

        if self.action in ["list", "retrieve", "create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserSerializer

    @action(detail=False, methods=["get"])
    def doctors(self, request):
        """List all doctors."""
        doctors = User.objects.filter(role="doctor", is_active=True)
        return Response(UserSerializer(doctors, many=True).data)

    @action(detail=False, methods=["get"])
    def patients(self, request):
        """List all patients."""
        patients = User.objects.filter(role="patient", is_active=True)
        return Response(UserSerializer(patients, many=True).data)
