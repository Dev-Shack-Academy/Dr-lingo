from django.db import models


class ChatRoom(models.Model):
    """
    Chat room for patient-doctor translation conversations.
    """

    ROOM_TYPES = [
        ("patient_doctor", "Patient-Doctor"),
        ("general", "General"),
    ]

    name = models.CharField(max_length=200)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default="patient_doctor")
    patient_language = models.CharField(max_length=50, default="en")
    doctor_language = models.CharField(max_length=50, default="en")
    rag_collection = models.ForeignKey(
        "api.Collection",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_rooms",
        help_text="RAG collection for cultural and medical context",
    )
    patient_name = models.CharField(max_length=200, blank=True, help_text="Patient name for context")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.patient_language} <-> {self.doctor_language})"


class ChatMessage(models.Model):
    """
    Individual messages in a chat room with translation support.
    """

    SENDER_TYPES = [
        ("patient", "Patient"),
        ("doctor", "Doctor"),
    ]

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender_type = models.CharField(max_length=10, choices=SENDER_TYPES)
    original_text = models.TextField()
    original_language = models.CharField(max_length=50)
    translated_text = models.TextField(blank=True, null=True)
    translated_language = models.CharField(max_length=50, blank=True, null=True)
    has_image = models.BooleanField(default=False)
    image_url = models.URLField(blank=True, null=True)
    image_description = models.TextField(blank=True, null=True)
    has_audio = models.BooleanField(default=False)
    audio_file = models.FileField(upload_to="chat_audio/", null=True, blank=True)
    audio_duration = models.FloatField(null=True, blank=True, help_text="Duration in seconds")
    audio_transcription = models.TextField(blank=True, help_text="Transcribed text from audio")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def audio_url(self):
        """Return full URL for audio file."""
        if self.audio_file:
            return self.audio_file.url
        return None

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender_type} - {self.original_text[:50]}"
