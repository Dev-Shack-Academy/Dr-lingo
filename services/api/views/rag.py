import logging

from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from api.models import Collection, CollectionItem
from api.serializers import CollectionItemSerializer, CollectionSerializer, RAGQuerySerializer
from api.services.rag_service import RAGService
from api.utils.pdf_utils import extract_text_from_pdf

logger = logging.getLogger(__name__)

# Check if Celery is available for async processing
CELERY_ENABLED = getattr(settings, "CELERY_BROKER_URL", None) is not None


class CollectionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing RAG collections."""

    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        from api.permissions import IsAdmin

        if self.action and self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
            "add_document",
            "reindex",
            "query",
            "query_and_answer",
        ]:
            return [IsAdmin()]
        return super().get_permissions()

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser, JSONParser])
    def add_document(self, request, pk=None):
        """Add a document to the collection. Uses Celery for async processing of PDFs."""
        collection = self.get_object()

        logger.info("=== ADD DOCUMENT REQUEST ===")
        logger.info(f"Content-Type: {request.content_type}")

        name = request.data.get("name")
        content = request.data.get("content")
        file_obj = request.FILES.get("file")
        description = request.data.get("description", "")
        metadata = request.data.get("metadata", {})
        async_mode = request.data.get("async", "true").lower() in ("true", "1", "yes")

        logger.info(f"Parsed: name={name}, file_obj={file_obj}, content_len={len(content) if content else 0}")

        # Handle PDF file upload - always process async due to potential OCR
        if file_obj and file_obj.name.lower().endswith(".pdf"):
            if not name:
                name = file_obj.name.replace(".pdf", "").replace(".PDF", "")

            if CELERY_ENABLED:
                # Save file and process asynchronously
                from api.tasks.pdf_tasks import process_pdf_document_async, save_uploaded_pdf

                try:
                    file_path = save_uploaded_pdf(file_obj)
                    task = process_pdf_document_async.delay(
                        collection_id=collection.id,
                        file_path=file_path,
                        name=name,
                        description=description,
                        metadata=metadata or {},
                    )

                    return Response(
                        {
                            "status": "processing",
                            "message": "PDF uploaded and queued for processing. Text extraction (including OCR if needed) will run in background.",
                            "task_id": task.id,
                            "name": name,
                        },
                        status=status.HTTP_202_ACCEPTED,
                    )
                except Exception as e:
                    logger.error(f"Failed to queue PDF processing: {e}", exc_info=True)
                    return Response(
                        {"error": f"Failed to queue PDF processing: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
            else:
                # Synchronous fallback - try direct extraction only
                try:
                    logger.info(f"Extracting text from PDF (sync): {file_obj.name}, size={file_obj.size}")
                    content = extract_text_from_pdf(file_obj)
                    logger.info(f"PDF extraction result: {len(content) if content else 0} characters")
                    if not content:
                        return Response(
                            {
                                "error": "Could not extract text from PDF. It may be a scanned document requiring OCR. Enable Celery for async OCR processing."
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                except Exception as e:
                    logger.error(f"PDF extraction failed: {e}", exc_info=True)
                    return Response({"error": f"Failed to process PDF: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        if not name or not content:
            return Response(
                {
                    "error": "Name and content (or a PDF file) are required",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Create item without embedding first if async mode
            if async_mode and CELERY_ENABLED:
                item = CollectionItem.objects.create(
                    collection=collection,
                    name=name,
                    content=content,
                    description=description,
                    metadata=metadata,
                    embedding=None,  # Will be generated async
                )

                # Queue embedding generation
                from api.tasks.rag_tasks import process_document_async

                process_document_async.delay(document_id=item.id)

                serializer = CollectionItemSerializer(item)
                return Response(
                    {
                        **serializer.data,
                        "status": "processing",
                        "message": "Document added, embedding generation queued",
                    },
                    status=status.HTTP_202_ACCEPTED,
                )

            # Synchronous processing (default)
            rag_service = RAGService(collection)
            items = rag_service.add_document(name=name, content=content, description=description, metadata=metadata)

            serializer = CollectionItemSerializer(items, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"])
    def query(self, request, pk=None):
        """Query the collection and return relevant documents."""
        collection = self.get_object()

        serializer = RAGQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        query_text = serializer.validated_data["query"]
        top_k = serializer.validated_data.get("top_k", 5)

        try:
            rag_service = RAGService(collection)
            results = rag_service.query(query_text, top_k=top_k)

            return Response(
                {
                    "query": query_text,
                    "results": [
                        {
                            "name": r["name"],
                            "content": r["content"],
                            "similarity": r["similarity"],
                            "metadata": r["metadata"],
                        }
                        for r in results
                    ],
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error querying collection: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"])
    def query_and_answer(self, request, pk=None):
        """Query the collection and generate an answer using RAG."""
        collection = self.get_object()

        serializer = RAGQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        query_text = serializer.validated_data["query"]
        top_k = serializer.validated_data.get("top_k", 5)

        try:
            rag_service = RAGService(collection)
            result = rag_service.query_and_answer(query_text, top_k=top_k)

            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in query_and_answer: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"])
    def reindex(self, request, pk=None):
        """Reindex all documents in the collection. Requires Celery."""
        collection = self.get_object()

        if not CELERY_ENABLED:
            return Response(
                {"error": "Celery is not configured. Reindexing requires background processing."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            from api.tasks.rag_tasks import reindex_collection

            task = reindex_collection.delay(collection_id=collection.id)
            return Response(
                {
                    "status": "processing",
                    "message": f"Reindexing started for collection '{collection.name}'",
                    "task_id": task.id,
                    "document_count": collection.items.count(),
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except Exception as e:
            logger.error(f"Error starting reindex: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CollectionItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing collection items."""

    queryset = CollectionItem.objects.all()
    serializer_class = CollectionItemSerializer

    def get_queryset(self):
        """Filter items by collection if specified."""
        queryset = super().get_queryset()
        collection_id = self.request.query_params.get("collection")
        if collection_id:
            queryset = queryset.filter(collection_id=collection_id)
        return queryset

    def perform_create(self, serializer):
        """Trigger background embedding generation for the new item."""
        item = serializer.save()

        # Queue embedding generation
        from api.tasks.rag_tasks import process_document_async

        process_document_async.delay(document_id=item.id)
