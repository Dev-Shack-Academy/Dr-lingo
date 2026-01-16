import logging

from pypdf import PdfReader

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_obj) -> str:
    """
    Extract text content from a PDF file object.
    Tries direct text extraction first, falls back to OCR for scanned PDFs.

    Args:
        file_obj: A file-like object containing PDF data.

    Returns:
        str: Extracted text content.
    """
    try:
        # First, try direct text extraction (for text-based PDFs)
        file_obj.seek(0)  # Reset file pointer
        reader = PdfReader(file_obj)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"

        text = text.strip()

        # If we got text, return it
        if text:
            logger.info(f"Extracted {len(text)} characters using direct text extraction")
            return text

        # If no text found, try OCR for scanned PDFs
        logger.info("No text found with direct extraction, attempting OCR...")
        return extract_text_with_ocr(file_obj)

    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise ValueError(f"Could not extract text from PDF: {str(e)}")


def extract_text_with_ocr(file_obj) -> str:
    """
    Extract text from a scanned PDF using OCR.

    Args:
        file_obj: A file-like object containing PDF data.

    Returns:
        str: Extracted text content via OCR.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
    except ImportError:
        logger.warning("OCR dependencies not installed. Install with: pip install pdf2image pytesseract")
        raise ValueError(
            "This PDF appears to be scanned/image-based and requires OCR. "
            "OCR dependencies (pdf2image, pytesseract) are not installed. "
            "Please install them or use a text-based PDF."
        )

    try:
        file_obj.seek(0)
        pdf_bytes = file_obj.read()

        # Convert PDF pages to images
        logger.info("Converting PDF to images for OCR...")
        images = convert_from_bytes(pdf_bytes, dpi=200)

        text = ""
        for i, image in enumerate(images):
            logger.info(f"Running OCR on page {i + 1}/{len(images)}...")
            page_text = pytesseract.image_to_string(image)
            if page_text:
                text += page_text + "\n"

        text = text.strip()
        logger.info(f"OCR extracted {len(text)} characters from {len(images)} pages")
        return text

    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        raise ValueError(f"OCR extraction failed: {str(e)}")
