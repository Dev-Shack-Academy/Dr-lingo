import hashlib
import logging

from django.core.cache import cache

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    queue="rag",
)
def process_document_async(self, document_id: int):
    """
    Process a document and generate embeddings in the background.

    This task:
    1. Loads the document from database
    2. Chunks the content if needed
    3. Generates embeddings using Gemini/Ollama
    4. Stores embeddings in the database
    5. Publishes event

    Args:
        document_id: ID of the CollectionItem to process

    Returns:
        dict with processing result
    """
    from api.events import publish_event
    from api.models import CollectionItem
    from api.services.rag_service import RAGService

    logger.info(f"Processing document {document_id}")

    try:
        item = CollectionItem.objects.get(id=document_id)

        # Check if already processed
        if item.embedding:
            logger.info(f"Document {document_id} already has embeddings")
            return {"status": "already_processed", "document_id": document_id}

        # Generate embedding
        rag_service = RAGService(item.collection)
        embedding = rag_service._generate_embedding(item.content)

        # Store embedding
        item.embedding = embedding
        item.save()

        # Publish event
        publish_event(
            "document.processed",
            {
                "document_id": document_id,
                "collection_id": item.collection_id,
                "name": item.name,
            },
        )

        logger.info(f"Document {document_id} processed successfully")

        return {
            "status": "success",
            "document_id": document_id,
            "embedding_size": len(embedding) if embedding else 0,
        }

    except CollectionItem.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        return {"status": "error", "error": "Document not found"}

    except Exception as e:
        logger.error(f"Document processing failed for {document_id}: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    queue="rag",
)
def generate_embeddings_async(self, collection_id: int):
    """
    Generate embeddings for all documents in a collection.

    Args:
        collection_id: ID of the Collection to process

    Returns:
        dict with processing summary
    """
    from api.models import Collection, CollectionItem

    logger.info(f"Generating embeddings for collection {collection_id}")

    try:
        collection = Collection.objects.get(id=collection_id)
        items = CollectionItem.objects.filter(
            collection=collection,
            embedding__isnull=True,
        )

        processed = 0
        failed = 0

        for item in items:
            try:
                # Queue individual document processing
                process_document_async.delay(item.id)
                processed += 1
            except Exception as e:
                logger.error(f"Failed to queue document {item.id}: {e}")
                failed += 1

        logger.info(f"Collection {collection_id}: queued {processed} documents, " f"{failed} failed")

        return {
            "status": "success",
            "collection_id": collection_id,
            "queued": processed,
            "failed": failed,
        }

    except Collection.DoesNotExist:
        logger.error(f"Collection {collection_id} not found")
        return {"status": "error", "error": "Collection not found"}


@shared_task(queue="rag")
def reindex_collection(collection_id: int):
    """
    Reindex all documents in a collection.

    Useful when:
    - Embedding model changes
    - Collection settings change
    - Manual reindex requested
    """
    from api.models import Collection, CollectionItem

    logger.info(f"Reindexing collection {collection_id}")

    try:
        collection = Collection.objects.get(id=collection_id)

        # Clear existing embeddings
        CollectionItem.objects.filter(collection=collection).update(embedding=None)

        # Regenerate all embeddings
        generate_embeddings_async.delay(collection_id)

        return {
            "status": "success",
            "collection_id": collection_id,
            "message": "Reindex started",
        }

    except Collection.DoesNotExist:
        return {"status": "error", "error": "Collection not found"}


@shared_task(queue="rag")
def cache_rag_query(collection_id: int, query: str, results: list):
    """
    Cache RAG query results for faster retrieval.

    Args:
        collection_id: Collection ID
        query: The query string
        results: Query results to cache
    """
    cache_key = f"rag:{collection_id}:{hashlib.sha256(query.encode()).hexdigest()[:16]}"
    cache.set(cache_key, results, timeout=1800)  # 30 minutes

    return {"status": "cached", "cache_key": cache_key}
