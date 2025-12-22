from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "preferred_language",
            "phone_number",
            "medical_license",
            "patient_id",
            "department",
            "is_active",
            "is_superuser",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined", "is_superuser"]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "role",
            "preferred_language",
            "phone_number",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "preferred_language",
            "phone_number",
            "medical_license",
            "patient_id",
            "department",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class TokenSerializer(serializers.Serializer):
    """Serializer for JWT tokens."""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
