"""
PDF Processing Tasks

Handles PDF text extraction including OCR for scanned documents.
"""

import logging
import os

from django.conf import settings

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=2,
    queue="default",
    soft_time_limit=1800,  # 30 min soft limit
    time_limit=2000,  # 33 min hard limit
)
def process_pdf_document_async(
    self,
    collection_id: int,
    file_path: str,
    name: str,
    description: str = "",
    metadata: dict = None,
):
    """
    Process a PDF document asynchronously, extracting text and creating a collection item.

    Supports both text-based PDFs and scanned PDFs (via OCR).

    Args:
        collection_id: ID of the collection to add the document to
        file_path: Path to the uploaded PDF file
        name: Name for the document
        description: Optional description
        metadata: Optional metadata dict

    Returns:
        dict with processing result
    """
    from api.models import Collection
    from api.services.rag import get_rag_service

    logger.info(f"Starting PDF processing for: {name}")

    try:
        collection = Collection.objects.get(id=collection_id)
    except Collection.DoesNotExist:
        logger.error(f"Collection {collection_id} not found")
        return {"success": False, "error": "Collection not found"}

    try:
        # Extract text from PDF
        content = extract_pdf_text(file_path)

        if not content:
            logger.error(f"No text extracted from PDF: {name}")
            return {"success": False, "error": "Could not extract text from PDF"}

        logger.info(f"Extracted {len(content)} characters from PDF: {name}")

        # Create the collection item with embedding
        rag_service = get_rag_service(collection)
        items = rag_service.add_document(
            name=name,
            content=content,
            description=description,
            metadata=metadata or {},
        )

        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)

        # Publish event
        try:
            from api.events import publish_event

            publish_event(
                "document.processed",
                {
                    "collection_id": collection_id,
                    "document_name": name,
                    "content_length": len(content),
                    "items_created": len(items),
                },
            )
        except Exception as e:
            logger.warning(f"Failed to publish document.processed event: {e}")

        logger.info(f"PDF processing complete: {name}, created {len(items)} items")
        return {
            "success": True,
            "name": name,
            "content_length": len(content),
            "items_created": len(items),
        }

    except Exception as e:
        logger.error(f"PDF processing failed for {name}: {e}", exc_info=True)
        # Clean up temp file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise


def extract_pdf_text(file_path: str) -> str:
    """
    Extract text from a PDF file.
    Tries direct extraction first, falls back to OCR for scanned PDFs.

    Args:
        file_path: Path to the PDF file

    Returns:
        Extracted text content
    """
    from pypdf import PdfReader

    logger.info(f"Extracting text from PDF: {file_path}")

    # First try direct text extraction
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"

        text = text.strip()
        if text:
            logger.info(f"Direct extraction successful: {len(text)} characters")
            return text
    except Exception as e:
        logger.warning(f"Direct PDF extraction failed: {e}")

    # Fall back to OCR
    logger.info("No text found, attempting OCR extraction...")
    return extract_pdf_with_ocr(file_path)


def extract_pdf_with_ocr(file_path: str) -> str:
    """
    Extract text from a scanned PDF using OCR.
    Processes pages one at a time to avoid memory issues.

    Args:
        file_path: Path to the PDF file

    Returns:
        Extracted text via OCR
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError:
        logger.error("OCR dependencies not installed")
        raise ValueError(
            "This PDF appears to be scanned/image-based. "
            "OCR dependencies (pdf2image, pytesseract) are not installed. "
            "Install with: poetry add pdf2image pytesseract && sudo apt-get install tesseract-ocr poppler-utils"
        )

    try:
        from pypdf import PdfReader

        # Get page count first
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)
        logger.info(f"PDF has {total_pages} pages, processing with OCR...")

        text = ""

        # Process one page at a time to avoid memory issues
        for page_num in range(1, total_pages + 1):
            logger.info(f"OCR processing page {page_num}/{total_pages}")
            try:
                # Convert single page at lower DPI to save memory
                images = convert_from_path(
                    file_path,
                    dpi=150,  # Lower DPI to reduce memory
                    first_page=page_num,
                    last_page=page_num,
                )

                if images:
                    page_text = pytesseract.image_to_string(images[0])
                    if page_text:
                        text += page_text + "\n"
                    # Explicitly delete to free memory
                    del images

            except Exception as e:
                logger.warning(f"Failed to OCR page {page_num}: {e}")
                continue

        text = text.strip()
        logger.info(f"OCR extraction complete: {len(text)} characters from {total_pages} pages")
        return text

    except Exception as e:
        logger.error(f"OCR extraction failed: {e}", exc_info=True)
        raise ValueError(f"OCR extraction failed: {str(e)}")


def save_uploaded_pdf(file_obj) -> str:
    """
    Save an uploaded PDF file to a temporary location for async processing.

    Args:
        file_obj: Django UploadedFile object

    Returns:
        Path to the saved file
    """
    # Create temp directory if it doesn't exist
    temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_uploads")
    os.makedirs(temp_dir, exist_ok=True)

    # Generate unique filename
    import uuid

    filename = f"{uuid.uuid4()}_{file_obj.name}"
    file_path = os.path.join(temp_dir, filename)

    # Save the file
    with open(file_path, "wb") as f:
        for chunk in file_obj.chunks():
            f.write(chunk)

    logger.info(f"Saved uploaded PDF to: {file_path}")
    return file_path
