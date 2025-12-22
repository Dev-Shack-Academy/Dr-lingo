from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from api.models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""

    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for custom User model."""

    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "preferred_language",
        "is_active",
        "date_joined",
    ]
    list_filter = ["role", "is_active", "is_staff", "preferred_language", "date_joined"]
    search_fields = ["username", "email", "first_name", "last_name", "patient_id", "medical_license"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "email", "phone_number")}),
        ("Role & Language", {"fields": ("role", "preferred_language")}),
        (
            "Role-Specific",
            {
                "fields": ("medical_license", "department", "patient_id"),
                "classes": ("collapse",),
            },
        ),
        (
            "Permissions",
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
                "classes": ("collapse",),
            },
        ),
        ("Important Dates", {"fields": ("last_login", "date_joined"), "classes": ("collapse",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "role",
                    "preferred_language",
                ),
            },
        ),
    )

    inlines = [UserProfileInline]

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)
