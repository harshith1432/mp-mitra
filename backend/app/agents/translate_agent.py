"""
MP MITRA — Translation Agent
==============================
Uses deep-translator (Google Translate free API) for all Indian languages.
No API key required. Falls back gracefully on error.
"""
import os
from typing import Optional

try:
    from deep_translator import GoogleTranslator
    _translator_available = True
except ImportError:
    _translator_available = False

try:
    from langdetect import detect as langdetect_detect
    _langdetect_available = True
except ImportError:
    _langdetect_available = False


# Language code mapping for deep-translator (some codes differ from WhatsApp)
_CODE_MAP = {
    "kn": "kn", "hi": "hi", "ta": "ta", "te": "te", "ml": "ml",
    "bn": "bn", "mr": "mr", "gu": "gu", "pa": "pa", "or": "or",
    "as": "as", "ur": "ur", "ne": "ne", "si": "si", "mai": "hi",  # Maithili → Hindi fallback
    "sat": "en", "ks": "ur", "sd": "sd", "kok": "mr", "doi": "hi",
    "mni": "bn", "bo": "hi", "en": "en",
}


def detect_language(text: str) -> str:
    """Detect language of input text. Returns ISO 639-1 code."""
    if not text or len(text) < 3:
        return "en"
    if _langdetect_available:
        try:
            return langdetect_detect(text)
        except Exception:
            pass
    return "en"


def translate_to_english(text: str, source_lang: str = "auto") -> str:
    """Translate any Indian language text to English."""
    if not text or not text.strip():
        return text
    if source_lang == "en" or source_lang == "english":
        return text
    if not _translator_available:
        return text  # graceful degradation

    src = _CODE_MAP.get(source_lang, "auto")
    try:
        result = GoogleTranslator(source=src, target="en").translate(text)
        return result or text
    except Exception as e:
        print(f"[Translation Error] {e}")
        return text


def translate_from_english(text: str, target_lang: str) -> str:
    """Translate English text to any Indian language."""
    if not text or not text.strip():
        return text
    if target_lang == "en" or target_lang == "english":
        return text
    if not _translator_available:
        return text  # graceful degradation

    tgt = _CODE_MAP.get(target_lang, "en")
    if tgt == "en":
        return text

    try:
        # Split long text into chunks (Google Translate limit ~5000 chars)
        if len(text) > 4000:
            chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
            translated_chunks = []
            for chunk in chunks:
                result = GoogleTranslator(source="en", target=tgt).translate(chunk)
                translated_chunks.append(result or chunk)
            return " ".join(translated_chunks)
        else:
            result = GoogleTranslator(source="en", target=tgt).translate(text)
            return result or text
    except Exception as e:
        print(f"[Translation Error] {e}")
        return text  # return original English on error


def translate_text(text: str, source: str, target: str) -> str:
    """Generic translate from any language to any language."""
    if source == target:
        return text
    en_text = translate_to_english(text, source) if source != "en" else text
    if target == "en":
        return en_text
    return translate_from_english(en_text, target)
