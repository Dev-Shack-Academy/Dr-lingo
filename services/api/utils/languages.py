"""
Centralized language definitions for the application.
Single source of truth for language codes and names.
"""

# Language code to full name mapping
# Used for translation prompts, dataset imports, and display
LANGUAGE_NAMES: dict[str, str] = {
    # South African Languages (Official)
    "zul": "isiZulu",
    "xho": "isiXhosa",
    "afr": "Afrikaans",
    "sot": "Sesotho",
    "tsn": "Setswana",
    "nso": "Sepedi",
    "ssw": "siSwati",
    "ven": "Tshivenda",
    "tso": "Xitsonga",
    "nbl": "isiNdebele",
    # International Languages
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "zh": "Chinese",
    "ar": "Arabic",
    "hi": "Hindi",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
}

# South African language codes only (for dataset imports)
SA_LANGUAGE_CODES = ["zul", "xho", "afr", "sot", "tsn", "nso", "ssw", "ven", "tso", "nbl"]


def get_language_name(code: str) -> str:
    """Convert language code to full name. Returns code if not found."""
    return LANGUAGE_NAMES.get(code, code)


def get_language_code(name: str) -> str | None:
    """Convert language name to code. Returns None if not found."""
    for code, lang_name in LANGUAGE_NAMES.items():
        if lang_name.lower() == name.lower():
            return code
    return None
