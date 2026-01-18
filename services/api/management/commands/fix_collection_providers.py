"""
Management command to fix existing collections with mismatched embedding providers.

This command updates collections that have Ollama provider/models but should be using
Gemini (or vice versa) based on the current AI_PROVIDER setting.
"""

import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from api.models import Collection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fix existing collections with mismatched embedding providers based on AI_PROVIDER setting"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without making changes",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update even if provider matches (useful for updating model names)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        force = options["force"]

        ai_provider = getattr(settings, "AI_PROVIDER", "ollama").lower()
        self.stdout.write(f"\nCurrent AI_PROVIDER: {ai_provider}")

        # Define expected values based on AI_PROVIDER
        if ai_provider == "gemini":
            expected_provider = Collection.EmbeddingProvider.GEMINI
            expected_embedding_model = "text-embedding-004"
            expected_completion_model = "gemini-2.0-flash"
            expected_dimensions = 768
        else:  # ollama
            expected_provider = Collection.EmbeddingProvider.OLLAMA
            expected_embedding_model = getattr(settings, "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:latest")
            expected_completion_model = getattr(settings, "OLLAMA_COMPLETION_MODEL", "granite3.3:8b")
            expected_dimensions = 768

        self.stdout.write(f"Expected provider: {expected_provider}")
        self.stdout.write(f"Expected embedding model: {expected_embedding_model}")
        self.stdout.write(f"Expected completion model: {expected_completion_model}\n")

        # Find collections that need updating
        collections = Collection.objects.all()
        updated_count = 0
        skipped_count = 0

        for collection in collections:
            needs_update = False
            changes = []

            # Check if provider matches
            if collection.embedding_provider != expected_provider:
                needs_update = True
                changes.append(f"  Provider: {collection.embedding_provider} → {expected_provider}")

            # Check if embedding model matches
            if collection.embedding_model != expected_embedding_model or force:
                if collection.embedding_model != expected_embedding_model:
                    needs_update = True
                changes.append(f"  Embedding model: {collection.embedding_model} → {expected_embedding_model}")

            # Check if completion model matches
            if collection.completion_model != expected_completion_model or force:
                if collection.completion_model != expected_completion_model:
                    needs_update = True
                changes.append(f"  Completion model: {collection.completion_model} → {expected_completion_model}")

            # Check dimensions
            if collection.embedding_dimensions != expected_dimensions:
                needs_update = True
                changes.append(f"  Dimensions: {collection.embedding_dimensions} → {expected_dimensions}")

            if needs_update or force:
                self.stdout.write(self.style.WARNING(f"\nCollection: {collection.name} (ID: {collection.id})"))
                for change in changes:
                    self.stdout.write(change)

                if not dry_run:
                    collection.embedding_provider = expected_provider
                    collection.embedding_model = expected_embedding_model
                    collection.completion_model = expected_completion_model
                    collection.embedding_dimensions = expected_dimensions
                    collection.save()

                    # Check if items need re-embedding
                    items_with_embeddings = collection.items.exclude(embedding__isnull=True).count()

                    if items_with_embeddings > 0:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ⚠️  This collection has {items_with_embeddings} items with embeddings."
                            )
                        )
                        self.stdout.write(
                            self.style.WARNING(
                                f"     Run 'python manage.py reindex_collection {collection.id}' to regenerate embeddings."
                            )
                        )

                    self.stdout.write(self.style.SUCCESS("  ✓ Updated"))
                else:
                    self.stdout.write(self.style.NOTICE("  (dry-run, no changes made)"))

                updated_count += 1
            else:
                skipped_count += 1

        # Summary
        self.stdout.write("\n" + "=" * 60)
        if dry_run:
            self.stdout.write(self.style.NOTICE(f"\nDRY RUN: {updated_count} collections would be updated"))
            self.stdout.write(f"{skipped_count} collections already correct")
            self.stdout.write("\nRun without --dry-run to apply changes")
        else:
            self.stdout.write(self.style.SUCCESS(f"\n✓ Updated {updated_count} collections"))
            self.stdout.write(f"✓ {skipped_count} collections already correct")

            if updated_count > 0:
                self.stdout.write(
                    self.style.WARNING("\n⚠️  IMPORTANT: Collections with existing embeddings need to be reindexed!")
                )
                self.stdout.write("Run: python manage.py reindex_collection <collection_id>")
