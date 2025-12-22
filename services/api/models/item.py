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
