from django.conf import settings
from django.db import models


class Collection(models.Model):
    """RAG Collection for document embeddings and retrieval."""

    class CollectionType(models.TextChoices):
        KNOWLEDGE_BASE = "knowledge_base", "Knowledge Base"
        PATIENT_CONTEXT = "patient_context", "Patient Context"

    class EmbeddingProvider(models.TextChoices):
        OPENAI = "openai", "OpenAI"
        GEMINI = "gemini", "Google Gemini"
        OLLAMA = "ollama", "Ollama (Local)"

    class ChunkingStrategy(models.TextChoices):
        FIXED_LENGTH = "fixed-length", "Fixed Length"
        WINDOW = "window", "Window"
        NO_CHUNKING = "no-chunking", "No Chunking"

    name = models.CharField(max_length=191, unique=True)
    description = models.TextField()
    collection_type = models.CharField(
        max_length=50,
        choices=CollectionType.choices,
        default=CollectionType.KNOWLEDGE_BASE,
        help_text="Knowledge Base: global reference data. Patient Context: per-chat patient details.",
    )
    is_global = models.BooleanField(
        default=True, help_text="Global collections are used for all translations. Non-global are chat-specific."
    )
    chat_room = models.ForeignKey(
        "ChatRoom",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patient_contexts",
        help_text="For patient context collections, link to specific chat room.",
    )
    knowledge_bases = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="linked_patient_contexts",
        limit_choices_to={"collection_type": "knowledge_base"},
        help_text="Knowledge base collections to use with this patient context.",
    )
    embedding_provider = models.CharField(
        max_length=100, choices=EmbeddingProvider.choices, default=EmbeddingProvider.OLLAMA
    )
    embedding_model = models.CharField(max_length=100, default="nomic-embed-text:latest")
    embedding_dimensions = models.PositiveIntegerField(default=768)
    completion_model = models.CharField(max_length=100, default="granite3.3:8b")
    chunking_strategy = models.CharField(
        max_length=100, choices=ChunkingStrategy.choices, default=ChunkingStrategy.FIXED_LENGTH
    )
    chunk_length = models.PositiveIntegerField(default=1000, null=True, blank=True)
    chunk_overlap = models.PositiveIntegerField(default=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Override save to set intelligent defaults based on AI_PROVIDER setting.

        If embedding_provider/embedding_model are not explicitly set (still at defaults),
        update them based on the global AI_PROVIDER setting.
        """
        # Only set defaults for new collections (no pk yet)
        if not self.pk:
            ai_provider = getattr(settings, "AI_PROVIDER", "ollama").lower()

            # If still using default Ollama values, update based on AI_PROVIDER
            if self.embedding_provider == self.EmbeddingProvider.OLLAMA:
                if ai_provider == "gemini":
                    self.embedding_provider = self.EmbeddingProvider.GEMINI
                    self.embedding_model = "text-embedding-004"
                    self.embedding_dimensions = 768
                    self.completion_model = "gemini-2.0-flash"
                elif ai_provider == "ollama":
                    # Keep Ollama defaults but ensure they're from settings
                    self.embedding_provider = self.EmbeddingProvider.OLLAMA
                    self.embedding_model = getattr(settings, "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:latest")
                    self.embedding_dimensions = 768
                    self.completion_model = getattr(settings, "OLLAMA_COMPLETION_MODEL", "granite3.3:8b")

        super().save(*args, **kwargs)


class CollectionItem(models.Model):
    """Individual document/item in a RAG collection."""

    name = models.CharField(max_length=191)
    description = models.TextField(blank=True)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="items")
    content = models.TextField()
    metadata = models.JSONField(null=True, blank=True)
    embedding = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.collection.name}"
