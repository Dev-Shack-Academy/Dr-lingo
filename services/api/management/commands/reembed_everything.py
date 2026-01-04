import logging

from django.core.management.base import BaseCommand

from api.models import Collection, CollectionItem
from api.tasks.rag_tasks import process_document_async

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Re-embed items that have null embeddings or belong to a specified collection"

    def add_arguments(self, parser):
        parser.add_argument(
            "--collection",
            type=str,
            help="Filter by collection name",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Re-embed all items, even those with existing embeddings",
        )
        parser.add_argument(
            "--async",
            dest="async_mode",
            action="store_true",
            help="Run re-embedding asynchronously via Celery",
        )

    def handle(self, *args, **options):
        collection_name = options.get("collection")
        all_items = options.get("all")
        async_mode = options.get("async_mode")

        items = CollectionItem.objects.all()

        if collection_name:
            try:
                collection = Collection.objects.get(name=collection_name)
                items = items.filter(collection=collection)
                self.stdout.write(self.style.SUCCESS(f"Filtering by collection: {collection_name}"))
            except Collection.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Collection '{collection_name}' not found."))
                return

        if not all_items:
            items = items.filter(embedding__isnull=True)

        count = items.count()
        if count == 0:
            self.stdout.write(self.style.WARNING("No items found to re-embed."))
            return

        self.stdout.write(self.style.HTTP_INFO(f"Found {count} items to process."))

        for item in items:
            self.stdout.write(f"Processing: {item.name} (ID: {item.id})")
            try:
                if async_mode:
                    process_document_async.delay(document_id=item.id)
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Queued async processing for {item.id}"))
                else:
                    # Run synchronously using .apply() to mimic behavior of remediate_rag.py
                    # or call task function directly if preferred.
                    # .apply() is safer as it respects task decorators.
                    result = process_document_async.apply(args=[item.id]).result
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Result for {item.id}: {result}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Error processing {item.id}: {e}"))

        self.stdout.write(self.style.SUCCESS("\nProcessing complete."))
