"""
Management command to ensure a superuser exists.
Creates superuser from environment variables if it doesn't exist.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ensures a superuser exists (creates if not present)"

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not all([username, email, password]):
            self.stdout.write(
                self.style.WARNING("Superuser environment variables not set. Skipping superuser creation.")
            )
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" already exists.'))
            return

        try:
            User.objects.create_superuser(username=username, email=email, password=password, role="admin")
            self.stdout.write(self.style.SUCCESS(f'✅ Superuser "{username}" created successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to create superuser: {e}"))
