from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with role-based access control.

    Roles:
    - patient: Can send messages, view own conversations
    - doctor: Can send messages, view patient context, get AI assistance
    - admin: Full access to all features
    """

    class Role(models.TextChoices):
        PATIENT = "patient", "Patient"
        DOCTOR = "doctor", "Doctor"
        ADMIN = "admin", "Administrator"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PATIENT,
    )
    preferred_language = models.CharField(
        max_length=10,
        default="en",
        help_text="User's preferred language code",
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Contact phone number",
    )

    # Role-specific fields
    medical_license = models.CharField(
        max_length=50,
        blank=True,
        help_text="Medical license number (for doctors)",
    )
    patient_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Patient ID (for patients)",
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text="Department (for doctors)",
    )

    class Meta:
        db_table = "auth_user"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_patient(self) -> bool:
        return self.role == self.Role.PATIENT

    @property
    def is_doctor(self) -> bool:
        return self.role == self.Role.DOCTOR

    @property
    def is_admin_user(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

    def can_access_rag(self) -> bool:
        """Check if user can access RAG features."""
        return self.role in [self.Role.DOCTOR, self.Role.ADMIN] or self.is_superuser

    def can_view_patient_context(self) -> bool:
        """Check if user can view patient context."""
        return self.role in [self.Role.DOCTOR, self.Role.ADMIN] or self.is_superuser

    def can_get_ai_assistance(self) -> bool:
        """Check if user can request AI assistance."""
        return self.role in [self.Role.DOCTOR, self.Role.ADMIN] or self.is_superuser

    def is_verified(self) -> bool:
        """
        Check if user has completed OTP verification.
        """
        try:
            from django_otp import user_has_device

            return user_has_device(self, confirmed=True)
        except ImportError:
            # django-otp not installed, assume verified
            return True


class UserProfile(models.Model):
    """Extended profile information for users."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    # Cultural preferences
    cultural_background = models.TextField(
        blank=True,
        help_text="Cultural background and preferences",
    )
    communication_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="Communication style preferences",
    )

    # Medical info (for patients)
    medical_conditions = models.TextField(
        blank=True,
        help_text="Known medical conditions",
    )
    allergies = models.TextField(
        blank=True,
        help_text="Known allergies",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profile"

    def __str__(self):
        return f"Profile for {self.user.username}"
