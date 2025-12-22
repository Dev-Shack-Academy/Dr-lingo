"""
Django management command to seed the database with sample data.

Usage:
    python manage.py seed_data

This command creates sample items in the database for testing and demonstration.
"""

from django.core.management.base import BaseCommand

from api.models import Item


class Command(BaseCommand):
    help = "Seeds the database with sample items"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding database with sample items...")

        # Clear existing items
        Item.objects.all().delete()
        self.stdout.write(self.style.WARNING("Cleared existing items"))

        # Sample items to create
        sample_items = [
            {
                "name": "Welcome Item",
                "description": "This is a sample item created to demonstrate the full-stack integration between React and Django. You can create, read, update, and delete items through the API.",
            },
            {
                "name": "dr-lingo Project",
                "description": "Use this scaffold as a starting point for your dr-lingo project. The client and services are already connected and ready to extend with your features.",
            },
            {
                "name": "API Example",
                "description": "This item was fetched from the Django services using the API service module. Check out src/services/api.js to see how API calls are made.",
            },
            {
                "name": "Database Integration",
                "description": "All items are stored in PostgreSQL database. The Django ORM handles all database operations, making it easy to work with data.",
            },
            {
                "name": "Ready to Build",
                "description": "Everything is set up and working! Start building your features by adding new models, API endpoints, and React components.",
            },
        ]

        # Create items
        created_count = 0
        for item_data in sample_items:
            item = Item.objects.create(**item_data)
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"Created item: {item.name}"))

        self.stdout.write(self.style.SUCCESS(f"\nSuccessfully created {created_count} sample items!"))
