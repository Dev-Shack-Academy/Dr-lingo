import logging

from api.utils import LANGUAGE_NAMES
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    queue="rag",
)
def import_hf_dataset_async(
    self,
    lang_code: str,
    collection_name: str | None = None,
    split: str = "train",
    limit: int | None = None,
    hf_token: str | None = None,
):
    """
    Import a South African language dataset from Hugging Face asynchronously.

    This task:
    1. Loads the dataset from Hugging Face (dsfsi-anv/za-african-next-voices)
    2. Creates or retrieves a RAG collection
    3. Imports transcripts as collection items
    4. Queues embedding generation for each item
    5. Publishes events for tracking progress

    Args:
        lang_code: Language code (zul, sot, xho, afr, nso, tsn, ssw, ven, nbl, tso)
        collection_name: Custom collection name (optional)
        split: Dataset split to import (train or dev_test)
        limit: Maximum number of items to import (optional)
        hf_token: Hugging Face API token for authentication (optional, uses settings.HF_TOKEN if not provided)

    Returns:
        dict with import results
    """
    from django.conf import settings

    from api.events import publish_event
    from api.models import Collection, CollectionItem

    if lang_code not in LANGUAGE_NAMES:
        return {
            "status": "error",
            "error": f"Unsupported language code: {lang_code}",
            "supported": list(LANGUAGE_NAMES.keys()),
        }

    lang_name = LANGUAGE_NAMES[lang_code]
    collection_name = collection_name or f"{lang_name} Language Dataset"

    # Use provided token or fall back to settings
    hf_token = hf_token or getattr(settings, "HF_TOKEN", "")

    logger.info(f"Starting async import of {lang_name} ({lang_code}) dataset")

    # Publish start event
    publish_event(
        "dataset.import_started",
        {
            "lang_code": lang_code,
            "lang_name": lang_name,
            "collection_name": collection_name,
            "split": split,
        },
    )

    try:
        # Check for required dependencies
        try:
            from datasets import load_dataset
        except ImportError:
            return {
                "status": "error",
                "error": "datasets library not installed",
            }

        # Authenticate with Hugging Face if token provided
        if hf_token:
            try:
                from huggingface_hub import login

                login(token=hf_token)
            except Exception as e:
                logger.warning(f"HF authentication failed: {e}")

        # Determine embedding provider from settings
        ai_provider = getattr(settings, "AI_PROVIDER", "gemini")
        if ai_provider == "ollama":
            embedding_provider = Collection.EmbeddingProvider.OLLAMA
            embedding_model = getattr(settings, "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:v1.5")
            embedding_dimensions = 768  # nomic-embed-text outputs 768 dimensions
        else:
            embedding_provider = Collection.EmbeddingProvider.GEMINI
            embedding_model = "text-embedding-004"
            embedding_dimensions = 768

        # Create or get collection
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
                "embedding_dimensions": embedding_dimensions,
                "chunking_strategy": Collection.ChunkingStrategy.NO_CHUNKING,
            },
        )

        # Load dataset
        repo_id = "dsfsi-anv/za-african-next-voices"
        try:
            ds = load_dataset(repo_id, lang_code, split=split)
        except Exception as e:
            error_msg = str(e)
            if "gated dataset" in error_msg.lower():
                logger.error(f"Gated dataset access denied for {lang_code}")
                publish_event(
                    "dataset.import_failed",
                    {
                        "lang_code": lang_code,
                        "lang_name": lang_name,
                        "error": (f"GATED DATASET - Request access at: " f"https://huggingface.co/datasets/{repo_id}"),
                    },
                )
                return {
                    "status": "error",
                    "error": "gated_dataset",
                    "message": (
                        f"This is a gated dataset. Visit "
                        f"https://huggingface.co/datasets/{repo_id} "
                        f"to request access, then try again."
                    ),
                }
            raise

        created_count = 0
        skipped_count = 0
        error_count = 0

        for idx, item in enumerate(ds):
            if limit and idx >= limit:
                break

            try:
                # Extract transcript
                transcript = None
                for field in ["transcription", "text", "sentence", "transcript"]:
                    if field in item and item[field]:
                        transcript = item[field]
                        break

                if not transcript or not transcript.strip():
                    skipped_count += 1
                    continue

                content = transcript.strip()
                item_name = f"transcript_{idx:06d}"

                # Check if exists
                if CollectionItem.objects.filter(collection=collection, name=item_name).exists():
                    skipped_count += 1
                    continue

                # Extract metadata
                metadata = {
                    "source": repo_id,
                    "lang_code": lang_code,
                    "index": idx,
                }
                for key in ["speaker_id", "gender", "age", "duration"]:
                    if key in item and isinstance(item[key], (str, int, float, bool)):
                        metadata[key] = item[key]

                # Create item without embedding (will be processed async)
                item_obj = CollectionItem.objects.create(
                    collection=collection,
                    name=item_name,
                    description=f"Transcript from {repo_id} ({lang_code}, index {idx})",
                    content=content,
                    metadata=metadata,
                    embedding=None,
                )

                # Queue embedding generation
                from api.tasks.rag_tasks import process_document_async

                process_document_async.delay(item_obj.id)
                created_count += 1

            except Exception as e:
                error_count += 1
                logger.error(f"Error processing item {idx}: {e}")

        # Publish completion event
        publish_event(
            "dataset.import_completed",
            {
                "lang_code": lang_code,
                "lang_name": lang_name,
                "collection_id": collection.id,
                "collection_name": collection_name,
                "created": created_count,
                "skipped": skipped_count,
                "errors": error_count,
            },
        )

        logger.info(
            f"Import completed for {lang_name}: "
            f"{created_count} created, {skipped_count} skipped, {error_count} errors"
        )

        return {
            "status": "success",
            "lang_code": lang_code,
            "lang_name": lang_name,
            "collection_id": collection.id,
            "collection_name": collection_name,
            "created": created_count,
            "skipped": skipped_count,
            "errors": error_count,
        }

    except Exception as e:
        logger.error(f"Dataset import failed for {lang_code}: {e}")

        publish_event(
            "dataset.import_failed",
            {
                "lang_code": lang_code,
                "lang_name": lang_name,
                "error": str(e),
            },
        )

        raise self.retry(exc=e)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    queue="rag",
)
def import_knowledge_base_projection_async(
    self,
    lang_code: str,
    collection_name: str | None = None,
    split: str = "train",
    limit: int | None = None,
    hf_token: str | None = None,
):
    """
    Import Knowledge Base Projection dataset from Hugging Face asynchronously.

    This task:
    1. Loads the dataset from Hugging Face (sello-ralethe/Knowledge_Base_Projection)
    2. Creates or retrieves a RAG collection
    3. Imports text content as collection items
    4. Queues embedding generation for each item
    5. Publishes events for tracking progress

    Args:
        lang_code: Language code (zul, xho, nso, sot, eng)
        collection_name: Custom collection name (optional)
        split: Dataset split to import (train)
        limit: Maximum number of items to import (optional)
        hf_token: Hugging Face API token for authentication (optional)

    Returns:
        dict with import results
    """
    from django.conf import settings

    from api.events import publish_event
    from api.models import Collection, CollectionItem

    # Supported languages for Knowledge Base Projection
    KB_LANGUAGES = {"zul": "isiZulu", "xho": "isiXhosa", "nso": "Sepedi", "sot": "SeSotho", "eng": "English"}

    if lang_code not in KB_LANGUAGES:
        return {
            "status": "error",
            "error": f"Unsupported language code: {lang_code}",
            "supported": list(KB_LANGUAGES.keys()),
        }

    lang_name = KB_LANGUAGES[lang_code]
    collection_name = collection_name or f"{lang_name} Knowledge Base"

    # Use provided token or fall back to settings
    hf_token = hf_token or getattr(settings, "HF_TOKEN", "")

    logger.info(f"Starting async import of {lang_name} ({lang_code}) Knowledge Base")

    # Publish start event
    publish_event(
        "dataset.kb_import_started",
        {
            "lang_code": lang_code,
            "lang_name": lang_name,
            "collection_name": collection_name,
            "split": split,
        },
    )

    try:
        # Check for required dependencies
        try:
            from datasets import load_dataset
        except ImportError:
            return {
                "status": "error",
                "error": "datasets library not installed",
            }

        # Authenticate with Hugging Face if token provided
        if hf_token:
            try:
                from huggingface_hub import login

                login(token=hf_token)
            except Exception as e:
                logger.warning(f"HF authentication failed: {e}")

        # Determine embedding provider from settings
        ai_provider = getattr(settings, "AI_PROVIDER", "gemini")
        if ai_provider == "ollama":
            embedding_provider = Collection.EmbeddingProvider.OLLAMA
            embedding_model = getattr(settings, "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:v1.5")
            embedding_dimensions = 768
        else:
            embedding_provider = Collection.EmbeddingProvider.GEMINI
            embedding_model = "text-embedding-004"
            embedding_dimensions = 768

        # Create or get collection
        collection, created = Collection.objects.get_or_create(
            name=collection_name,
            defaults={
                "description": (
                    f"Cross-lingual knowledge base for {lang_name} from sello-ralethe/Knowledge_Base_Projection. "
                    f"Contains parallel text corpora, projected knowledge bases from ConceptNet and DBpedia, "
                    f"verbalized triples, and translated question-answer pairs created using LeNS-Align technique."
                ),
                "collection_type": Collection.CollectionType.KNOWLEDGE_BASE,
                "is_global": True,
                "embedding_provider": embedding_provider,
                "embedding_model": embedding_model,
                "embedding_dimensions": embedding_dimensions,
                "chunking_strategy": Collection.ChunkingStrategy.NO_CHUNKING,
            },
        )

        # Load dataset
        repo_id = "sello-ralethe/Knowledge_Base_Projection"
        try:
            ds = load_dataset(repo_id, split=split)
            # Filter for the specific language if language column exists
            if "language" in ds.column_names:
                ds = ds.filter(lambda x: x["language"] == lang_code)
        except Exception as e:
            error_msg = str(e)
            if "gated dataset" in error_msg.lower():
                logger.error(f"Gated dataset access denied for {lang_code}")
                publish_event(
                    "dataset.kb_import_failed",
                    {
                        "lang_code": lang_code,
                        "lang_name": lang_name,
                        "error": (f"GATED DATASET - Request access at: " f"https://huggingface.co/datasets/{repo_id}"),
                    },
                )
                return {
                    "status": "error",
                    "error": "gated_dataset",
                    "message": (
                        f"This is a gated dataset. Visit "
                        f"https://huggingface.co/datasets/{repo_id} "
                        f"to request access, then try again."
                    ),
                }
            raise

        created_count = 0
        skipped_count = 0
        error_count = 0

        for idx, item in enumerate(ds):
            if limit and idx >= limit:
                break

            try:
                # Extract text content
                text_content = item.get("text", "").strip()

                if not text_content:
                    skipped_count += 1
                    continue

                item_name = f"kb_projection_{lang_code}_{idx:06d}"

                # Check if exists
                if CollectionItem.objects.filter(collection=collection, name=item_name).exists():
                    skipped_count += 1
                    continue

                # Extract metadata
                metadata = {
                    "source": repo_id,
                    "language": lang_code,
                    "index": idx,
                }

                # Add any additional fields as metadata
                for key, value in item.items():
                    if key != "text" and value is not None and isinstance(value, (str, int, float, bool)):
                        metadata[key] = value

                # Create item without embedding (will be processed async)
                item_obj = CollectionItem.objects.create(
                    collection=collection,
                    name=item_name,
                    description=f"Knowledge base text from {lang_code} projection (index {idx})",
                    content=text_content,
                    metadata=metadata,
                    embedding=None,
                )

                # Queue embedding generation
                from api.tasks.rag_tasks import process_document_async

                process_document_async.delay(item_obj.id)
                created_count += 1

            except Exception as e:
                error_count += 1
                logger.error(f"Error processing item {idx}: {e}")

        # Publish completion event
        publish_event(
            "dataset.kb_import_completed",
            {
                "lang_code": lang_code,
                "lang_name": lang_name,
                "collection_id": collection.id,
                "collection_name": collection_name,
                "created": created_count,
                "skipped": skipped_count,
                "errors": error_count,
            },
        )

        logger.info(
            f"KB import completed for {lang_name}: "
            f"{created_count} created, {skipped_count} skipped, {error_count} errors"
        )

        return {
            "status": "success",
            "lang_code": lang_code,
            "lang_name": lang_name,
            "collection_id": collection.id,
            "collection_name": collection_name,
            "created": created_count,
            "skipped": skipped_count,
            "errors": error_count,
        }

    except Exception as e:
        logger.error(f"KB dataset import failed for {lang_code}: {e}")

        publish_event(
            "dataset.kb_import_failed",
            {
                "lang_code": lang_code,
                "lang_name": lang_name,
                "error": str(e),
            },
        )

        raise self.retry(exc=e)


@shared_task(queue="rag")
def import_all_hf_languages(
    split: str = "train",
    limit: int | None = None,
    hf_token: str | None = None,
):
    """
    Import all supported South African languages from Hugging Face.

    Queues individual import tasks for each language.

    Args:
        split: Dataset split to import
        limit: Maximum items per language
        hf_token: Hugging Face API token (optional, uses settings.HF_TOKEN if not provided)

    Returns:
        dict with queued task info
    """
    from django.conf import settings

    from api.events import publish_event

    # Use provided token or fall back to settings
    hf_token = hf_token or getattr(settings, "HF_TOKEN", "")

    queued = []
    for lang_code in LANGUAGE_NAMES.keys():
        import_hf_dataset_async.delay(
            lang_code=lang_code,
            split=split,
            limit=limit,
            hf_token=hf_token if hf_token else None,
        )
        queued.append(lang_code)

    publish_event(
        "dataset.batch_import_started",
        {
            "languages": queued,
            "split": split,
            "limit": limit,
        },
    )

    return {
        "status": "queued",
        "languages": queued,
        "count": len(queued),
    }


@shared_task(queue="rag")
def import_all_kb_languages(
    split: str = "train",
    limit: int | None = None,
    hf_token: str | None = None,
):
    """
    Import all supported languages from Knowledge Base Projection dataset.

    Queues individual import tasks for each language.

    Args:
        split: Dataset split to import
        limit: Maximum items per language
        hf_token: Hugging Face API token (optional)

    Returns:
        dict with queued task info
    """
    from django.conf import settings

    from api.events import publish_event

    # Use provided token or fall back to settings
    hf_token = hf_token or getattr(settings, "HF_TOKEN", "")

    # Knowledge Base Projection supported languages
    KB_LANGUAGES = ["zul", "xho", "nso", "sot", "eng"]

    queued = []
    for lang_code in KB_LANGUAGES:
        import_knowledge_base_projection_async.delay(
            lang_code=lang_code,
            split=split,
            limit=limit,
            hf_token=hf_token if hf_token else None,
        )
        queued.append(lang_code)

    publish_event(
        "dataset.kb_batch_import_started",
        {
            "languages": queued,
            "split": split,
            "limit": limit,
        },
    )

    return {
        "status": "queued",
        "languages": queued,
        "count": len(queued),
    }
