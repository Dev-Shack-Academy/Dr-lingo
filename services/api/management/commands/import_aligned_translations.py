import logging

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)

# Language codes supported by the EdinburghNLP/south-african-lang-id dataset
SUPPORTED_LANGUAGES = {"afrikaans": "Afrikaans", "english": "English", "xhosa": "isiXhosa"}

# Map to our standard language codes
LANG_CODE_MAPPING = {"afrikaans": "afr", "english": "eng", "xhosa": "xho"}


class Command(BaseCommand):
    help = "Import aligned multilingual translations from EdinburghNLP/south-african-lang-id dataset"

    def add_arguments(self, parser):
        parser.add_argument(
            "--languages",
            type=str,
            nargs="+",
            default=["english", "afrikaans"],  # Default to English-Afrikaans pair
            choices=list(SUPPORTED_LANGUAGES.keys()),
            help="Languages to import as aligned translations (default: english afrikaans)",
        )
        parser.add_argument(
            "--collection",
            type=str,
            default=None,  # Will be auto-generated based on language pair
            help="Collection name for aligned translations (default: auto-generated from language pair)",
        )
        parser.add_argument(
            "--split",
            type=str,
            default="train",
            help="Dataset split to import (default: train)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of aligned sets to import (useful for testing)",
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
        parser.add_argument(
            "--verify-alignment",
            action="store_true",
            help="Verify alignment quality before importing (checks length ratios)",
        )
        parser.add_argument(
            "--min-length-ratio",
            type=float,
            default=0.3,  # More lenient for cross-language alignment
            help="Minimum length ratio for alignment verification (default: 0.3)",
        )
        parser.add_argument(
            "--max-length-ratio",
            type=float,
            default=3.0,  # More lenient for cross-language alignment
            help="Maximum length ratio for alignment verification (default: 3.0)",
        )

    def handle(self, *args, **options):
        from django.conf import settings

        languages = options["languages"]
        collection_name = options["collection"]
        split = options["split"]
        limit = options["limit"]
        async_mode = options["async_mode"]
        verify_alignment = options["verify_alignment"]
        min_ratio = options["min_length_ratio"]
        max_ratio = options["max_length_ratio"]

        # Use provided token or fall back to settings
        hf_token = options["hf_token"] or getattr(settings, "HF_TOKEN", "")

        # Generate collection name if not provided
        if not collection_name:
            lang_names = [SUPPORTED_LANGUAGES[lang] for lang in languages]
            collection_name = f"{'-'.join(lang_names)} Aligned Translations"

        self.stdout.write(f"\n{'='*70}")
        self.stdout.write(self.style.HTTP_INFO("Importing Aligned Multilingual Translations"))
        self.stdout.write(f"{'='*70}")
        self.stdout.write("  Dataset: EdinburghNLP/south-african-lang-id")
        self.stdout.write(f"  Languages: {', '.join([SUPPORTED_LANGUAGES[lang] for lang in languages])}")
        self.stdout.write(f"  Language codes: {', '.join([LANG_CODE_MAPPING[lang] for lang in languages])}")
        self.stdout.write(f"  Split: {split}")
        self.stdout.write(f"  Collection: {collection_name}")
        self.stdout.write(f"  Limit: {limit or 'None'}")
        self.stdout.write(f"  Async mode: {async_mode}")
        self.stdout.write(f"  Verify alignment: {verify_alignment}")
        if verify_alignment:
            self.stdout.write(f"  Length ratio range: {min_ratio:.1f} - {max_ratio:.1f}")
        self.stdout.write(f"  HF Token: {'Configured' if hf_token else 'Not set'}")
        self.stdout.write(f"{'='*70}\n")

        # Check for required dependencies
        import importlib.util

        if importlib.util.find_spec("datasets") is None:
            raise CommandError("The 'datasets' library is required. Install it with:\n" "  pip install datasets")

        # Check AI provider connectivity
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
        collection = self._get_or_create_collection(collection_name, languages)

        # Load and process the aligned datasets
        self._import_aligned_datasets(
            collection, languages, split, limit, async_mode, verify_alignment, min_ratio, max_ratio
        )

        self.stdout.write(self.style.SUCCESS("\n✅ Aligned translation import completed!"))

    def _get_or_create_collection(self, collection_name, languages):
        """Create or retrieve the RAG collection for aligned translations."""
        from django.conf import settings

        from api.models import Collection

        # Determine embedding provider from settings
        ai_provider = getattr(settings, "AI_PROVIDER", "gemini")
        if ai_provider == "ollama":
            embedding_provider = Collection.EmbeddingProvider.OLLAMA
            embedding_model = getattr(settings, "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:latest")
            completion_model = getattr(settings, "OLLAMA_COMPLETION_MODEL", "granite3.3:8b")
            embedding_dimensions = 768
            self.stdout.write(f"Using Ollama embeddings: {embedding_model}")
        else:
            embedding_provider = Collection.EmbeddingProvider.GEMINI
            embedding_model = "text-embedding-004"
            completion_model = "gemini-2.0-flash-exp"
            embedding_dimensions = 768
            self.stdout.write(f"Using Gemini embeddings: {embedding_model}")

        lang_names = [SUPPORTED_LANGUAGES[lang] for lang in languages]
        lang_codes = [LANG_CODE_MAPPING[lang] for lang in languages]

        # Create language pair identifier for collection name
        lang_pair = "-".join(lang_names)

        # Collection name is already set correctly from handle method
        final_collection_name = collection_name

        collection, created = Collection.objects.get_or_create(
            name=final_collection_name,
            defaults={
                "description": (
                    f"Aligned bilingual translations between {lang_pair} "
                    f"from EdinburghNLP/south-african-lang-id dataset. "
                    f"Each item contains the same content translated between {len(languages)} languages, "
                    f"enabling cross-lingual RAG queries and improved bilingual understanding. "
                    f"Language codes: {', '.join(lang_codes)}."
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
            self.stdout.write(self.style.SUCCESS(f"Created new collection: {final_collection_name}"))
        else:
            self.stdout.write(self.style.WARNING(f"Using existing collection: {final_collection_name}"))
            item_count = collection.items.count()
            if item_count > 0:
                self.stdout.write(f"  Existing items: {item_count}")

        return collection

    def _import_aligned_datasets(
        self, collection, languages, split, limit, async_mode, verify_alignment, min_ratio, max_ratio
    ):
        """Load aligned datasets and import as multilingual items."""
        import os
        import time

        from datasets import load_dataset

        from api.services.rag import get_rag_service

        repo_id = "EdinburghNLP/south-african-lang-id"

        self.stdout.write("\nLoading datasets from Hugging Face...")
        self.stdout.write(f"  Repository: {repo_id}")

        # Set extended timeout for Hugging Face downloads
        os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "120")

        # Load all language datasets
        datasets = {}
        for lang in languages:
            self.stdout.write(f"  Loading {SUPPORTED_LANGUAGES[lang]} ({lang})...")

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    ds = load_dataset(repo_id, lang, split=split)
                    datasets[lang] = ds
                    self.stdout.write(self.style.SUCCESS(f"    ✓ {SUPPORTED_LANGUAGES[lang]}: {len(ds)} items"))
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        self.stdout.write(self.style.WARNING(f"    Retry {attempt + 1}/{max_retries} for {lang}..."))
                        time.sleep(2)
                        continue
                    else:
                        raise CommandError(f"Failed to load {lang} after {max_retries} attempts: {e}")

        # Verify all datasets have same length
        dataset_lengths = {lang: len(ds) for lang, ds in datasets.items()}
        if len(set(dataset_lengths.values())) > 1:
            self.stdout.write(self.style.WARNING(f"Dataset lengths differ: {dataset_lengths}"))
            min_length = min(dataset_lengths.values())
            self.stdout.write(f"Will process {min_length} aligned items (shortest dataset)")
        else:
            min_length = list(dataset_lengths.values())[0]
            self.stdout.write(self.style.SUCCESS(f"All datasets aligned: {min_length} items each"))

        # Initialize RAG service for embedding generation (if not async)
        rag_service = None
        if not async_mode:
            try:
                rag_service = get_rag_service(collection)
                self.stdout.write("RAG service initialized for embedding generation")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"RAG service init failed: {e}"))
                self.stdout.write("Will create items without embeddings")

        # Process aligned items
        created_count = 0
        skipped_count = 0
        error_count = 0
        alignment_failed = 0
        embedding_success = 0
        embedding_failed = 0

        self.stdout.write(f"\nProcessing {min_length} aligned translation sets...")

        # Determine actual limit
        process_limit = min(limit, min_length) if limit else min_length

        for idx in range(process_limit):
            try:
                # Get aligned texts from all languages
                aligned_texts = {}
                for lang in languages:
                    item = datasets[lang][idx]
                    text = item.get("text", "").strip()
                    if not text:
                        self.stdout.write(self.style.WARNING(f"  ⚠ Item {idx}: Empty text in {lang}, skipping set"))
                        skipped_count += 1
                        break
                    aligned_texts[lang] = text

                # Skip if any language is missing text
                if len(aligned_texts) != len(languages):
                    continue

                # Verify alignment quality if requested
                if verify_alignment and len(aligned_texts) >= 2:
                    if not self._verify_alignment_quality(aligned_texts, min_ratio, max_ratio):
                        alignment_failed += 1
                        self.stdout.write(
                            self.style.WARNING(f"  ⚠ Item {idx}: Failed alignment verification, skipping")
                        )
                        continue

                # Process the aligned set
                result = self._process_aligned_item(collection, aligned_texts, idx, rag_service, async_mode, languages)

                if result == "created":
                    created_count += 1
                    embedding_success += 1
                    if (idx + 1) % 10 == 0:
                        self.stdout.write(self.style.SUCCESS(f"  ✓ Processed {idx + 1} aligned sets"))
                elif result == "created_no_embedding":
                    created_count += 1
                    embedding_failed += 1
                elif result == "skipped":
                    skipped_count += 1

            except Exception as e:
                error_count += 1
                logger.error(f"Error processing aligned set {idx}: {e}")
                self.stdout.write(self.style.ERROR(f"  ✗ Item {idx}: {e}"))

        # Summary
        self.stdout.write(f"\n{'='*70}")
        self.stdout.write(self.style.SUCCESS("Aligned Translation Import Summary:"))
        self.stdout.write(f"  Languages: {', '.join([SUPPORTED_LANGUAGES[lang] for lang in languages])}")
        self.stdout.write(f"  Created aligned sets: {created_count}")
        self.stdout.write(f"    - With embeddings: {embedding_success}")
        self.stdout.write(f"    - Without embeddings: {embedding_failed}")
        self.stdout.write(f"  Skipped: {skipped_count}")
        if verify_alignment:
            self.stdout.write(f"  Failed alignment verification: {alignment_failed}")
        self.stdout.write(f"  Errors: {error_count}")
        self.stdout.write(f"  Total items in collection: {collection.items.count()}")
        self.stdout.write(f"{'='*70}")

    def _verify_alignment_quality(self, aligned_texts, min_ratio, max_ratio):
        """Verify that texts are likely aligned translations based on length ratios."""
        texts = list(aligned_texts.values())
        if len(texts) < 2:
            return True

        # Check all pairwise length ratios
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                len1, len2 = len(texts[i]), len(texts[j])
                if len2 == 0:
                    return False
                ratio = len1 / len2
                if not (min_ratio <= ratio <= max_ratio):
                    return False

        return True

    def _process_aligned_item(self, collection, aligned_texts, idx, rag_service, async_mode, languages):
        """Process a single aligned translation set and add to collection."""
        from api.models import CollectionItem

        # Create combined content with all translations
        lang_codes = [LANG_CODE_MAPPING[lang] for lang in languages]

        # Format: "English: text\n\nAfrikaans: text\n\nisiXhosa: text"
        combined_content_parts = []
        for lang in languages:
            lang_name = SUPPORTED_LANGUAGES[lang]
            text = aligned_texts[lang]
            combined_content_parts.append(f"{lang_name}: {text}")

        combined_content = "\n\n".join(combined_content_parts)

        # Build metadata with all translations
        metadata = {
            "source": "EdinburghNLP/south-african-lang-id",
            "type": "aligned_translations",
            "languages": lang_codes,
            "index": idx,
        }

        # Add individual translations to metadata
        for lang in languages:
            lang_code = LANG_CODE_MAPPING[lang]
            metadata[f"text_{lang_code}"] = aligned_texts[lang]

        # Generate a unique name for this aligned set
        lang_suffix = "_".join(lang_codes)
        item_name = f"aligned_{lang_suffix}_{idx:06d}"

        # Check if item already exists
        if CollectionItem.objects.filter(collection=collection, name=item_name).exists():
            return "skipped"

        # Create description
        description = (
            f"Aligned translations (index {idx}) in {', '.join([SUPPORTED_LANGUAGES[lang] for lang in languages])}"
        )

        # Create the collection item
        if async_mode:
            # Create without embedding, queue for async processing
            item_obj = CollectionItem.objects.create(
                collection=collection,
                name=item_name,
                description=description,
                content=combined_content,
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
                    content=combined_content,
                    description=description,
                    metadata=metadata,
                )
            except Exception as e:
                # Fall back to creating without embedding
                logger.warning(f"Embedding failed for {item_name}: {e}")
                CollectionItem.objects.create(
                    collection=collection,
                    name=item_name,
                    description=description,
                    content=combined_content,
                    metadata=metadata,
                    embedding=None,
                )
                return "created_no_embedding"
        else:
            # Create without embedding
            CollectionItem.objects.create(
                collection=collection,
                name=item_name,
                description=description,
                content=combined_content,
                metadata=metadata,
                embedding=None,
            )
            return "created_no_embedding"

        return "created"
