import logging

from django.core.management.base import BaseCommand, CommandError

from api.models import Collection
from api.services.rag import get_rag_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Reindex a collection by regenerating all embeddings with current provider/model"

    def add_arguments(self, parser):
        parser.add_argument(
            "collection_id",
            type=int,
            help="ID of the collection to reindex",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )

    def handle(self, *args, **options):
        collection_id = options["collection_id"]
        dry_run = options["dry_run"]

        try:
            collection = Collection.objects.get(id=collection_id)
        except Collection.DoesNotExist:
            raise CommandError(f"Collection with ID {collection_id} does not exist")

        self.stdout.write(f"\nCollection: {collection.name}")
        self.stdout.write(f"Provider: {collection.embedding_provider}")
        self.stdout.write(f"Embedding Model: {collection.embedding_model}")
        self.stdout.write(f"Completion Model: {collection.completion_model}")
        self.stdout.write(f"Dimensions: {collection.embedding_dimensions}\n")

        items = collection.items.all()
        total_items = items.count()

        if total_items == 0:
            self.stdout.write(self.style.WARNING("No items to reindex"))
            return

        self.stdout.write(f"Found {total_items} items to reindex\n")

        if dry_run:
            self.stdout.write(self.style.NOTICE("DRY RUN - No changes will be made\n"))
            for i, item in enumerate(items, 1):
                self.stdout.write(f"  [{i}/{total_items}] {item.name}")
            self.stdout.write(f"\nRun without --dry-run to reindex {total_items} items")
            return

        # Get RAG service for this collection
        try:
            rag_service = get_rag_service(collection)
        except Exception as e:
            raise CommandError(f"Failed to initialize RAG service: {e}")

        # Reindex each item
        success_count = 0
        error_count = 0

        for i, item in enumerate(items, 1):
            try:
                self.stdout.write(f"[{i}/{total_items}] Reindexing: {item.name}...", ending="")

                # Generate new embedding
                embedding = rag_service._generate_embedding(item.content)
                item.embedding = embedding
                item.save()

                self.stdout.write(self.style.SUCCESS(" ✓"))
                success_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f" ✗ Error: {e}"))
                logger.error(f"Failed to reindex item {item.id}: {e}", exc_info=True)
                error_count += 1

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"✓ Successfully reindexed: {success_count} items"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"✗ Failed: {error_count} items"))
        self.stdout.write("")
