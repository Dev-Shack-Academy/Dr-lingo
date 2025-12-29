import logging

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.views.decorators.csrf import csrf_exempt
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


@csrf_exempt
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


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """
    Login using Django sessions (cookie-based auth with OTP).

    POST /api/auth/login/
    """
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    username = serializer.validated_data["username"]
    password = serializer.validated_data["password"]

    user = authenticate(request, username=username, password=password)
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

    # Log the user in (creates session)
    django_login(request, user)

    # Check OTP status - ALL users must set up OTP
    requires_otp_setup = False
    requires_otp_verify = False

    try:
        from django_otp.plugins.otp_totp.models import TOTPDevice

        has_otp_device = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
        if not has_otp_device:
            # User needs to set up OTP first
            requires_otp_setup = True
        else:
            # User has OTP, needs to verify
            requires_otp_verify = True
    except ImportError:
        pass

    return Response(
        {
            "user": UserSerializer(user).data,
            "requires_otp_setup": requires_otp_setup,
            "requires_otp_verify": requires_otp_verify,
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


@api_view(["POST"])
@permission_classes([AllowAny])
def logout(request):
    """
    Logout and clear session.

    POST /api/auth/logout/
    """
    django_logout(request)
    return Response({"status": "success", "message": "Logged out successfully"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_otp(request):
    """
    Verify OTP code for two-factor authentication.

    POST /api/auth/verify-otp/
    """
    otp_token = request.data.get("otp_token")
    if not otp_token:
        return Response(
            {"error": "OTP token is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from django_otp import devices_for_user

        # Try to verify the token against user's devices
        for device in devices_for_user(request.user):
            if device.verify_token(otp_token):
                # Mark the session as OTP-verified
                request.session["otp_device_id"] = device.persistent_id
                return Response(
                    {
                        "status": "success",
                        "user": UserSerializer(request.user).data,
                    }
                )

        return Response(
            {"error": "Invalid OTP code"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except ImportError:
        return Response(
            {"error": "OTP not configured on server"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def setup_otp(request):
    """
    Setup OTP device for user. Returns QR code for authenticator app.

    POST /api/auth/setup-otp/
    """
    try:
        import base64
        from io import BytesIO

        import qrcode
        import qrcode.image.svg
        from django_otp.plugins.otp_totp.models import TOTPDevice

        # Check if user already has a confirmed device
        existing_device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()
        if existing_device:
            return Response(
                {"error": "OTP is already set up for this account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delete any unconfirmed devices
        TOTPDevice.objects.filter(user=request.user, confirmed=False).delete()

        # Create new TOTP device
        device = TOTPDevice.objects.create(
            user=request.user,
            name="default",
            confirmed=False,
        )

        # Generate QR code
        config_url = device.config_url
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(config_url)
        qr.make(fit=True)

        # Create QR code image as base64
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return Response(
            {
                "qr_code": f"data:image/png;base64,{qr_base64}",
                "secret": device.key,
            }
        )
    except ImportError as e:
        logger.error(f"OTP setup failed - missing dependency: {e}")
        return Response(
            {"error": "OTP dependencies not installed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def confirm_otp_setup(request):
    """
    Confirm OTP setup by verifying a code from the authenticator app.

    POST /api/auth/confirm-otp-setup/
    """
    otp_token = request.data.get("otp_token")
    if not otp_token:
        return Response(
            {"error": "OTP token is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from django_otp.plugins.otp_totp.models import TOTPDevice

        # Get unconfirmed device
        device = TOTPDevice.objects.filter(user=request.user, confirmed=False).first()
        if not device:
            return Response(
                {"error": "No pending OTP setup found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the token
        if device.verify_token(otp_token):
            device.confirmed = True
            device.save()

            # Mark session as verified
            request.session["otp_device_id"] = device.persistent_id

            return Response(
                {
                    "success": True,
                    "message": "OTP setup complete",
                    "user": UserSerializer(request.user).data,
                }
            )

        return Response(
            {"error": "Invalid OTP code"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except ImportError:
        return Response(
            {"error": "OTP not configured on server"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


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
