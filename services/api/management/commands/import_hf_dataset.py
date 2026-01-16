import logging

from django.core.management.base import BaseCommand, CommandError

from api.utils import LANGUAGE_NAMES, SA_LANGUAGE_CODES

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import South African language datasets from Hugging Face into RAG knowledge base"

    def add_arguments(self, parser):
        parser.add_argument(
            "--lang",
            type=str,
            required=True,
            choices=SA_LANGUAGE_CODES,
            help="Language code to import (e.g., zul for isiZulu, sot for Sesotho)",
        )
        parser.add_argument(
            "--collection",
            type=str,
            default=None,
            help="Custom collection name (default: auto-generated from language)",
        )
        parser.add_argument(
            "--split",
            type=str,
            default="train",
            choices=["train", "dev_test"],
            help="Dataset split to import (default: train)",
        )
        parser.add_argument(
            "--streaming",
            action="store_true",
            help="Use streaming mode for large datasets",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of items to import (useful for testing)",
        )
        parser.add_argument(
            "--async",
            dest="async_mode",
            action="store_true",
            help="Process embeddings asynchronously using Celery",
        )
        parser.add_argument(
            "--hf-token",
            type=str,
            default=None,
            help="Hugging Face API token (optional, uses HF_TOKEN from settings if not provided)",
        )

    def handle(self, *args, **options):
        from django.conf import settings

        lang_code = options["lang"]
        lang_name = LANGUAGE_NAMES[lang_code]
        split = options["split"]
        limit = options["limit"]
        async_mode = options["async_mode"]

        # Auto-enable streaming when limit is set (avoids downloading entire dataset)
        streaming = options["streaming"]
        if limit and not streaming:
            streaming = True
            self.stdout.write(
                self.style.WARNING(f"Auto-enabling streaming mode (limit={limit} set, avoids full download)")
            )

        # Use provided token or fall back to settings
        hf_token = options["hf_token"] or getattr(settings, "HF_TOKEN", "")

        # Generate collection name if not provided
        collection_name = options["collection"] or f"{lang_name} Language Dataset"

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.HTTP_INFO(f"Importing {lang_name} ({lang_code}) dataset"))
        self.stdout.write(f"{'='*60}")
        self.stdout.write("  Dataset: dsfsi-anv/za-african-next-voices")
        self.stdout.write(f"  Language: {lang_name} ({lang_code})")
        self.stdout.write(f"  Split: {split}")
        self.stdout.write(f"  Collection: {collection_name}")
        self.stdout.write(f"  Streaming: {streaming}")
        self.stdout.write(f"  Limit: {limit or 'None'}")
        self.stdout.write(f"  Async mode: {async_mode}")
        self.stdout.write(f"  HF Token: {'Configured' if hf_token else 'Not set'}")
        self.stdout.write(f"{'='*60}\n")

        # Check for required dependencies
        import importlib.util

        if importlib.util.find_spec("datasets") is None:
            raise CommandError(
                "The 'datasets' library is required. Install it with:\n"
                "  pip install datasets[audio]==3.6.0\n"
                "  pip install ffmpeg ffmpeg-python"
            )

        # Check Ollama connectivity if using Ollama
        ai_provider = getattr(settings, "AI_PROVIDER", "gemini")
        if ai_provider == "ollama":
            self.stdout.write("Checking Ollama connectivity...")
            try:
                import requests

                ollama_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
                response = requests.get(f"{ollama_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = [m["name"] for m in response.json().get("models", [])]
                    self.stdout.write(self.style.SUCCESS(f"Ollama connected. Available models: {models}"))
                    embedding_model = getattr(settings, "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:v1.5")
                    if not any(embedding_model in m for m in models):
                        self.stdout.write(
                            self.style.WARNING(
                                f"Model '{embedding_model}' not found! Run: ollama pull {embedding_model}"
                            )
                        )
                else:
                    raise CommandError(f"Ollama returned status {response.status_code}")
            except requests.RequestException as e:
                raise CommandError(
                    f"Cannot connect to Ollama at {ollama_url}: {e}\n" f"Make sure Ollama is running: ollama serve"
                )

        # Authenticate with Hugging Face if token available
        if hf_token:
            try:
                from huggingface_hub import login

                login(token=hf_token)
                self.stdout.write(self.style.SUCCESS("Authenticated with Hugging Face"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"HF authentication failed: {e}"))

        # Create or get the collection
        collection = self._get_or_create_collection(collection_name, lang_code, lang_name)

        # Load and process the dataset
        self._import_dataset(collection, lang_code, split, streaming, limit, async_mode)

        self.stdout.write(self.style.SUCCESS(f"\n✅ Import completed for {lang_name}!"))

    def _get_or_create_collection(self, collection_name, lang_code, lang_name):
        """Create or retrieve the RAG collection for this dataset."""
        from django.conf import settings

        from api.models import Collection

        # Determine embedding provider from settings
        ai_provider = getattr(settings, "AI_PROVIDER", "gemini")
        if ai_provider == "ollama":
            embedding_provider = Collection.EmbeddingProvider.OLLAMA
            embedding_model = getattr(settings, "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:latest")
            completion_model = getattr(settings, "OLLAMA_COMPLETION_MODEL", "granite3.3:8b")
            embedding_dimensions = 768  # nomic-embed-text outputs 768 dimensions
            self.stdout.write(f"Using Ollama embeddings: {embedding_model}")
        else:
            embedding_provider = Collection.EmbeddingProvider.GEMINI
            embedding_model = "text-embedding-004"
            completion_model = "gemini-2.0-flash-exp"
            embedding_dimensions = 768
            self.stdout.write(f"Using Gemini embeddings: {embedding_model}")

        collection, created = Collection.objects.get_or_create(
            name=collection_name,
            defaults={
                "description": (
                    f"South African {lang_name} language dataset from Hugging Face. "
                    f"Source: dsfsi-anv/za-african-next-voices ({lang_code}). "
                    f"Contains transcripts and metadata for {lang_name} speech data."
                ),
                "collection_type": Collection.CollectionType.KNOWLEDGE_BASE,
                "is_global": True,
                "embedding_provider": embedding_provider,
                "embedding_model": embedding_model,
                "completion_model": completion_model,
                "embedding_dimensions": embedding_dimensions,
                "chunking_strategy": Collection.ChunkingStrategy.NO_CHUNKING,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created new collection: {collection_name}"))
        else:
            self.stdout.write(self.style.WARNING(f"Using existing collection: {collection_name}"))
            item_count = collection.items.count()
            if item_count > 0:
                self.stdout.write(f"  Existing items: {item_count}")

        return collection

    def _import_dataset(self, collection, lang_code, split, streaming, limit, async_mode):
        """Load dataset from Hugging Face and import into collection."""
        import os
        import time

        from datasets import Audio, load_dataset

        from api.services.rag import get_rag_service

        repo_id = "dsfsi-anv/za-african-next-voices"

        self.stdout.write("\nLoading dataset from Hugging Face...")
        self.stdout.write(f"  Repository: {repo_id}")
        self.stdout.write(f"  Configuration: {lang_code}")

        # Set extended timeout for Hugging Face downloads (default is 10s, too short!)
        os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "120")

        # Retry logic for network issues
        max_retries = 5
        retry_delay = 5  # seconds, will increase exponentially

        for attempt in range(max_retries):
            try:
                if streaming:
                    # Load in streaming mode WITHOUT decoding audio (avoids librosa dependency)
                    ds = load_dataset(repo_id, lang_code, split=split, streaming=True)
                    # Disable audio decoding - this avoids needing librosa/soundfile
                    # See: https://huggingface.co/docs/datasets/audio_load#disable-audio-decoding
                    try:
                        ds = ds.cast_column("audio", Audio(decode=False))
                        ds = ds.remove_columns(["audio"])
                        self.stdout.write("Disabled audio decoding and removed column (text-only import)")
                    except Exception:
                        pass  # Column might not exist
                    self.stdout.write(self.style.SUCCESS("Dataset loaded in streaming mode"))
                else:
                    ds = load_dataset(repo_id, lang_code, split=split)
                    total_items = len(ds)
                    self.stdout.write(self.style.SUCCESS(f"Dataset loaded: {total_items} items"))
                break  # Success, exit retry loop

            except Exception as e:
                error_msg = str(e)

                # Check for gated dataset error (no retry needed)
                if "gated dataset" in error_msg.lower():
                    raise CommandError(
                        f"This is a GATED DATASET - you need to request access first!\n\n"
                        f"Steps to get access:\n"
                        f"  1. Visit: https://huggingface.co/datasets/{repo_id}\n"
                        f"  2. Click 'Access repository' button\n"
                        f"  3. Accept the dataset terms/license\n"
                        f"  4. Wait for approval (usually instant for this dataset)\n"
                        f"  5. Ensure your HF_TOKEN has 'Read' permission\n\n"
                        f"Then run this command again."
                    )

                # Check for timeout/network errors (retry these)
                is_timeout = any(
                    x in error_msg.lower() for x in ["timeout", "timed out", "connection", "network", "reset by peer"]
                )

                if is_timeout and attempt < max_retries - 1:
                    wait_time = retry_delay * (2**attempt)  # Exponential backoff
                    self.stdout.write(
                        self.style.WARNING(
                            f"Network timeout (attempt {attempt + 1}/{max_retries}). " f"Retrying in {wait_time}s..."
                        )
                    )
                    time.sleep(wait_time)
                    continue

                # Final failure
                raise CommandError(f"Failed to load dataset after {attempt + 1} attempts: {e}")

        # Initialize RAG service for embedding generation (if not async)
        rag_service = None
        if not async_mode:
            try:
                rag_service = get_rag_service(collection)
                self.stdout.write("RAG service initialized for embedding generation")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"RAG service init failed: {e}"))
                self.stdout.write("Will create items without embeddings")

        # Process dataset items
        created_count = 0
        skipped_count = 0
        error_count = 0
        embedding_success = 0
        embedding_failed = 0

        self.stdout.write("\nProcessing items...")
        self.stdout.write("Fetching first item from dataset (this may take a moment for streaming)...")

        # Handle streaming vs non-streaming
        items_iterator = iter(ds) if streaming else ds

        for idx, item in enumerate(items_iterator):
            if idx == 0:
                self.stdout.write(self.style.SUCCESS("First item received from dataset"))

            if limit and idx >= limit:
                self.stdout.write(f"Reached limit of {limit} items")
                break

            try:
                self.stdout.write(f"  Processing item {idx}...")
                result = self._process_item(collection, item, idx, rag_service, async_mode)
                if result == "created":
                    created_count += 1
                    embedding_success += 1
                    # Show progress for each item
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Item {idx}: embedded successfully"))
                elif result == "created_no_embedding":
                    created_count += 1
                    embedding_failed += 1
                    self.stdout.write(self.style.WARNING(f"  ⚠ Item {idx}: created without embedding"))
                elif result == "skipped":
                    skipped_count += 1

                # Progress indicator every 10 items
                if (idx + 1) % 10 == 0:
                    self.stdout.write(
                        f"  --- Progress: {idx + 1} items processed "
                        f"(✓{embedding_success} ⚠{embedding_failed} ⊘{skipped_count}) ---"
                    )

            except Exception as e:
                error_count += 1
                logger.error(f"Error processing item {idx}: {e}")
                self.stdout.write(self.style.ERROR(f"  ✗ Item {idx}: {e}"))

        # Summary
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS("Import Summary:"))
        self.stdout.write(f"  Created: {created_count}")
        self.stdout.write(f"    - With embeddings: {embedding_success}")
        self.stdout.write(f"    - Without embeddings: {embedding_failed}")
        self.stdout.write(f"  Skipped: {skipped_count}")
        self.stdout.write(f"  Errors: {error_count}")
        self.stdout.write(f"  Total in collection: {collection.items.count()}")
        self.stdout.write(f"{'='*60}")

    def _process_item(self, collection, item, idx, rag_service, async_mode):
        """Process a single dataset item and add to collection."""
        from api.models import CollectionItem

        # Extract data from the dataset item
        # The za-african-next-voices dataset typically has:
        # - audio: audio data
        # - transcription or text: the transcript
        # - Other metadata fields

        # Try to get transcript from various possible field names
        transcript = None
        for field in ["transcription", "text", "sentence", "transcript"]:
            if field in item and item[field]:
                transcript = item[field]
                break

        if not transcript:
            return "skipped"

        # Build content and metadata
        content = transcript.strip()
        if not content:
            return "skipped"

        # Extract metadata
        metadata = {
            "source": "dsfsi-anv/za-african-next-voices",
            "index": idx,
        }

        # Add any additional fields as metadata
        for key in ["speaker_id", "gender", "age", "accent", "duration", "path", "audio_path"]:
            if key in item and item[key] is not None:
                # Handle non-serializable types
                value = item[key]
                if hasattr(value, "tolist"):  # numpy array
                    continue  # Skip audio data
                if isinstance(value, (str, int, float, bool)):
                    metadata[key] = value

        # Generate a unique name for this item
        item_name = f"transcript_{idx:06d}"

        # Check if item already exists
        if CollectionItem.objects.filter(collection=collection, name=item_name).exists():
            return "skipped"

        # Create the collection item
        if async_mode:
            # Create without embedding, queue for async processing
            item_obj = CollectionItem.objects.create(
                collection=collection,
                name=item_name,
                description=f"Transcript from za-african-next-voices dataset (index {idx})",
                content=content,
                metadata=metadata,
                embedding=None,
            )

            # Queue embedding generation
            from api.tasks.rag_tasks import process_document_async

            process_document_async.delay(document_id=item_obj.id)

        elif rag_service:
            # Synchronous with embedding
            try:
                rag_service.add_document(
                    name=item_name,
                    content=content,
                    description=f"Transcript from za-african-next-voices dataset (index {idx})",
                    metadata=metadata,
                )
            except Exception as e:
                # Fall back to creating without embedding
                logger.warning(f"Embedding failed for {item_name}: {e}")
                CollectionItem.objects.create(
                    collection=collection,
                    name=item_name,
                    description=f"Transcript from za-african-next-voices dataset (index {idx})",
                    content=content,
                    metadata=metadata,
                    embedding=None,
                )
                return "created_no_embedding"
        else:
            # Create without embedding
            CollectionItem.objects.create(
                collection=collection,
                name=item_name,
                description=f"Transcript from za-african-next-voices dataset (index {idx})",
                content=content,
                metadata=metadata,
                embedding=None,
            )
            return "created_no_embedding"

        return "created"
