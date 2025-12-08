"""
Django admin configuration for managing models through the admin interface.
"""

from django.contrib import admin

from .models import ChatMessage, ChatRoom, Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """Admin interface for Item model."""

    list_display = ["id", "name", "created_at", "updated_at"]
    search_fields = ["name", "description"]
    list_filter = ["created_at"]
    ordering = ["-created_at"]


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    """Admin interface for ChatRoom model."""

    list_display = ["id", "name", "room_type", "patient_language", "doctor_language", "is_active", "created_at"]
    search_fields = ["name"]
    list_filter = ["room_type", "is_active", "patient_language", "doctor_language", "created_at"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("name", "room_type", "is_active")}),
        ("Language Settings", {"fields": ("patient_language", "doctor_language")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin interface for ChatMessage model."""

    list_display = ["id", "room", "sender_type", "original_text_preview", "has_image", "created_at"]
    search_fields = ["original_text", "translated_text"]
    list_filter = ["sender_type", "has_image", "created_at", "room"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Message Information", {"fields": ("room", "sender_type")}),
        ("Original Content", {"fields": ("original_text", "original_language")}),
        ("Translation", {"fields": ("translated_text", "translated_language")}),
        ("Image Content", {"fields": ("has_image", "image_url", "image_description"), "classes": ("collapse",)}),
        ("Timestamp", {"fields": ("created_at",), "classes": ("collapse",)}),
    )
    readonly_fields = ["created_at"]

    def original_text_preview(self, obj):
        """Show preview of original text."""
        return obj.original_text[:50] + "..." if len(obj.original_text) > 50 else obj.original_text

    original_text_preview.short_description = "Original Text"
