from django.contrib import admin

from api.models import ChatMessage, ChatRoom


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    """Admin interface for ChatRoom model."""

    list_display = [
        "id",
        "name",
        "room_type",
        "patient_name",
        "patient_language",
        "doctor_language",
        "has_rag",
        "is_active",
        "created_at",
    ]
    search_fields = ["name", "patient_name"]
    list_filter = ["room_type", "is_active", "patient_language", "doctor_language", "created_at"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("name", "room_type", "is_active")}),
        ("Patient Information", {"fields": ("patient_name",)}),
        ("Language Settings", {"fields": ("patient_language", "doctor_language")}),
        ("RAG Configuration", {"fields": ("rag_collection",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    readonly_fields = ["created_at", "updated_at"]

    def has_rag(self, obj):
        """Show if room has RAG collection."""
        return obj.rag_collection is not None

    has_rag.boolean = True
    has_rag.short_description = "RAG Enabled"


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin interface for ChatMessage model."""

    list_display = ["id", "room", "sender_type", "original_text_preview", "has_image", "has_audio", "created_at"]
    search_fields = ["original_text", "translated_text", "audio_transcription"]
    list_filter = ["sender_type", "has_image", "has_audio", "created_at", "room"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Message Information", {"fields": ("room", "sender_type")}),
        ("Original Content", {"fields": ("original_text", "original_language")}),
        ("Translation", {"fields": ("translated_text", "translated_language")}),
        ("Image Content", {"fields": ("has_image", "image_url", "image_description"), "classes": ("collapse",)}),
        (
            "Audio Content",
            {"fields": ("has_audio", "audio_file", "audio_duration", "audio_transcription"), "classes": ("collapse",)},
        ),
        ("Timestamp", {"fields": ("created_at",), "classes": ("collapse",)}),
    )
    readonly_fields = ["created_at", "audio_transcription"]

    def original_text_preview(self, obj):
        """Show preview of original text."""
        return obj.original_text[:50] + "..." if len(obj.original_text) > 50 else obj.original_text

    original_text_preview.short_description = "Original Text"
