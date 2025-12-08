"""
Database models for the API.

Models define the structure of database tables and relationships.
Each model class represents a table, and each attribute represents a field.
"""

from django.db import models


class Item(models.Model):
    """
    Example model for demonstration purposes.

    Fields:
        name: The name of the item
        description: A detailed description
        created_at: Timestamp when created
        updated_at: Timestamp when last updated
    """

    name = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender_type} - {self.original_text[:50]}"
