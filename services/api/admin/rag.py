from django.contrib import admin

from api.models import Collection, CollectionItem


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    """Admin interface for Collection model."""

    list_display = [
        "id",
        "name",
        "embedding_provider",
        "embedding_model",
        "embedding_dimensions",
        "items_count",
        "created_at",
    ]
    search_fields = ["name", "description"]
    list_filter = ["embedding_provider", "chunking_strategy", "created_at"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("name", "description")}),
        ("Embedding Configuration", {"fields": ("embedding_provider", "embedding_model", "embedding_dimensions")}),
        ("Completion Configuration", {"fields": ("completion_model",)}),
        (
            "Chunking Configuration",
            {"fields": ("chunking_strategy", "chunk_length", "chunk_overlap"), "classes": ("collapse",)},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    readonly_fields = ["created_at", "updated_at"]

    def items_count(self, obj):
        """Show number of items in collection."""
        return obj.items.count()

    items_count.short_description = "Documents"


@admin.register(CollectionItem)
class CollectionItemAdmin(admin.ModelAdmin):
    """Admin interface for CollectionItem model."""

    list_display = ["id", "name", "collection", "content_preview", "has_embedding", "created_at"]
    search_fields = ["name", "description", "content"]
    list_filter = ["collection", "created_at"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("name", "description", "collection")}),
        ("Content", {"fields": ("content",)}),
        ("Metadata", {"fields": ("metadata",), "classes": ("collapse",)}),
        ("Embedding", {"fields": ("embedding_info",), "classes": ("collapse",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    readonly_fields = ["created_at", "updated_at", "embedding_info"]

    def content_preview(self, obj):
        """Show preview of content."""
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    content_preview.short_description = "Content Preview"

    def has_embedding(self, obj):
        """Show if item has embedding."""
        return obj.embedding is not None and len(obj.embedding) > 0

    has_embedding.boolean = True
    has_embedding.short_description = "Has Embedding"

    def embedding_info(self, obj):
        """Show embedding information."""
        if obj.embedding:
            return f"Vector with {len(obj.embedding)} dimensions"
        return "No embedding generated"

    embedding_info.short_description = "Embedding Info"
