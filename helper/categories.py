# helper/categories.py
"""
Product category normalisation.

The catalog scraper stored the Tokopedia breadcrumb in the `type` column as a
stringified Python list, e.g. "['Home', 'Kecantikan', 'Masker Wajah']". The most
specific (last) token is the real category, so we surface that instead of "Home".
"""
import ast
from typing import Any

FALLBACK_CATEGORY = "Skincare"


def normalize_category(raw: Any) -> str:
    """Return a clean, human-readable category from a raw `Product.type` value."""
    if raw is None:
        return FALLBACK_CATEGORY

    text = str(raw).strip()
    if not text or text.lower() in ("none", "nan"):
        return FALLBACK_CATEGORY

    if text.startswith("[") and text.endswith("]"):
        tokens = _parse_breadcrumb(text)
        if tokens:
            text = tokens[-1]

    cleaned = text.strip()
    return cleaned.title() if cleaned else FALLBACK_CATEGORY


def _parse_breadcrumb(text: str) -> list:
    """Best-effort parse of a stringified breadcrumb list into its tokens."""
    try:
        parsed = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return [token.strip().strip("'\"") for token in text.strip("[]").split(",")]

    if isinstance(parsed, (list, tuple)):
        return [str(token).strip() for token in parsed if str(token).strip()]
    return [str(parsed).strip()] if str(parsed).strip() else []
