from rest_framework import serializers

from api.models import Collection, CollectionItem


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for Collection model."""

    items_count = serializers.SerializerMethodField()
    chat_room_name = serializers.CharField(source="chat_room.name", read_only=True)
    knowledge_bases = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Collection.objects.filter(collection_type="knowledge_base"),
        required=False,
    )
    knowledge_bases_details = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = [
            "id",
            "name",
            "description",
            "collection_type",
            "is_global",
            "chat_room",
            "chat_room_name",
            "knowledge_bases",
            "knowledge_bases_details",
            "embedding_provider",
            "embedding_model",
            "embedding_dimensions",
            "completion_model",
            "chunking_strategy",
            "chunk_length",
            "chunk_overlap",
            "created_at",
            "updated_at",
            "items_count",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_items_count(self, obj):
        return obj.items.count()

    def get_knowledge_bases_details(self, obj):
        """Return details of linked knowledge bases."""
        if obj.collection_type != "patient_context":
            return []
        return [{"id": kb.id, "name": kb.name} for kb in obj.knowledge_bases.all()]


class CollectionItemSerializer(serializers.ModelSerializer):
    """Serializer for CollectionItem model."""

    collection_name = serializers.CharField(source="collection.name", read_only=True)

    class Meta:
        model = CollectionItem
        fields = [
            "id",
            "name",
            "description",
            "collection",
            "collection_name",
            "content",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "embedding"]


class RAGQuerySerializer(serializers.Serializer):
    """Serializer for RAG query requests."""

    query = serializers.CharField(required=True)
    top_k = serializers.IntegerField(default=5, min_value=1, max_value=20)
