from django.contrib import admin

from api.models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """Admin interface for Item model."""

    list_display = ["id", "name", "created_at", "updated_at"]
    search_fields = ["name", "description"]
    list_filter = ["created_at"]
    ordering = ["-created_at"]
