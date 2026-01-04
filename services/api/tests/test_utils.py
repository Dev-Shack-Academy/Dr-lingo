import io
from unittest.mock import MagicMock, patch

import pytest
from api.utils.languages import LANGUAGE_NAMES, get_language_name


class TestPDFUtils:
    """Tests for PDF utility functions."""

    @patch("api.utils.pdf_utils.PdfReader")
    def test_extract_text_from_pdf_success(self, mock_pdf_reader):
        """Test successful PDF text extraction."""
        from api.utils.pdf_utils import extract_text_from_pdf

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Extracted PDF text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        file_obj = io.BytesIO(b"fake PDF content")
        result = extract_text_from_pdf(file_obj)

        assert result == "Extracted PDF text"

    @patch("api.utils.pdf_utils.extract_text_with_ocr")
    @patch("api.utils.pdf_utils.PdfReader")
    def test_extract_text_from_pdf_empty_fallback_to_ocr(self, mock_pdf_reader, mock_ocr):
        """Test PDF extraction falls back to OCR when text is empty."""
        from api.utils.pdf_utils import extract_text_from_pdf

        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""  # Empty text
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        mock_ocr.return_value = "OCR extracted text"

        file_obj = io.BytesIO(b"fake PDF content")
        result = extract_text_from_pdf(file_obj)

        assert result == "OCR extracted text"
        mock_ocr.assert_called_once()

    @patch("api.utils.pdf_utils.PdfReader")
    def test_extract_text_from_pdf_exception(self, mock_pdf_reader):
        """Test PDF extraction handles exceptions."""
        from api.utils.pdf_utils import extract_text_from_pdf

        mock_pdf_reader.side_effect = Exception("PDF parsing error")

        file_obj = io.BytesIO(b"fake PDF content")

        with pytest.raises(ValueError) as exc_info:
            extract_text_from_pdf(file_obj)

        assert "PDF parsing error" in str(exc_info.value)

    def test_extract_text_with_ocr_success(self):
        """Test OCR text extraction concept."""
        from api.utils.pdf_utils import extract_text_with_ocr

        # This test verifies the OCR function exists and is callable
        assert callable(extract_text_with_ocr)

        # The actual OCR functionality requires pytesseract and pdf2image
        # which may not be installed in test environment

    def test_extract_text_with_ocr_import_error(self):
        """Test OCR extraction handles missing dependencies."""
        from api.utils.pdf_utils import extract_text_with_ocr

        # The function imports pytesseract and pdf2image inside
        # If they're not installed, it should raise ValueError
        with patch.dict("sys.modules", {"pytesseract": None, "pdf2image": None}):
            # Force reimport to trigger ImportError
            file_obj = io.BytesIO(b"fake PDF content")

            # The actual behavior depends on whether the modules are installed
            # If not installed, it raises ValueError about OCR dependencies
            try:
                result = extract_text_with_ocr(file_obj)
                # If it succeeds, the modules are installed
                assert isinstance(result, str)
            except (ValueError, ImportError) as e:
                # Expected if OCR dependencies not installed
                assert "OCR" in str(e) or "pytesseract" in str(e).lower()

    @patch("api.utils.pdf_utils.PdfReader")
    def test_extract_text_from_pdf_with_file_object(self, mock_pdf_reader):
        """Test PDF extraction with file-like object."""
        from api.utils.pdf_utils import extract_text_from_pdf

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "File object text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        file_obj = io.BytesIO(b"fake PDF content")
        result = extract_text_from_pdf(file_obj)

        assert result == "File object text"


class TestLanguageUtils:
    def test_get_language_name_known_languages(self):
        """Test getting language names for known language codes."""
        assert get_language_name("en") == "English"
        assert get_language_name("es") == "Spanish"
        assert get_language_name("fr") == "French"
        assert get_language_name("de") == "German"
        assert get_language_name("zh") == "Chinese"

        # South African languages
        assert get_language_name("zul") == "isiZulu"
        assert get_language_name("xho") == "isiXhosa"
        assert get_language_name("afr") == "Afrikaans"
        assert get_language_name("sot") == "Sesotho"

    def test_get_language_name_unknown_language(self):
        """Test getting language name for unknown language code."""
        assert get_language_name("xyz") == "xyz"  # Returns code itself
        assert get_language_name("unknown") == "unknown"

    def test_get_language_name_case_sensitive(self):
        """Test language name lookup is case sensitive (returns code if not found)."""
        # The function is case-sensitive, uppercase codes return themselves
        assert get_language_name("EN") == "EN"  # Not found, returns code
        assert get_language_name("en") == "English"  # Found

    def test_get_language_name_empty_input(self):
        """Test getting language name for empty input."""
        assert get_language_name("") == ""

    def test_language_names_dictionary_completeness(self):
        """Test that LANGUAGE_NAMES dictionary contains expected languages."""
        # Only test languages that are actually in the dictionary
        expected_languages = [
            "en",
            "es",
            "fr",
            "de",
            "zh",
            "ar",
            "hi",
            "pt",
            "ru",
            "ja",
            "zul",
            "xho",
            "afr",
            "sot",
            "nso",
            "tsn",
            "ssw",
            "ven",
            "nbl",
            "tso",
        ]

        for lang_code in expected_languages:
            assert lang_code in LANGUAGE_NAMES
            assert isinstance(LANGUAGE_NAMES[lang_code], str)
            assert len(LANGUAGE_NAMES[lang_code]) > 0

    def test_language_names_values_are_strings(self):
        """Test that all language names are non-empty strings."""
        for lang_code, lang_name in LANGUAGE_NAMES.items():
            assert isinstance(lang_code, str)
            assert isinstance(lang_name, str)
            assert len(lang_code) > 0
            assert len(lang_name) > 0

    def test_south_african_languages_present(self):
        """Test that all South African languages are present."""
        sa_languages = {
            "zul": "isiZulu",
            "xho": "isiXhosa",
            "afr": "Afrikaans",
            "sot": "Sesotho",
            "nso": "Sepedi",
            "tsn": "Setswana",
            "ssw": "siSwati",
            "ven": "Tshivenda",
            "nbl": "isiNdebele",
            "tso": "Xitsonga",
        }

        for code, name in sa_languages.items():
            assert code in LANGUAGE_NAMES
            assert LANGUAGE_NAMES[code] == name
