# helper/skin_types.py
"""
Best-effort inference of the skin types a product targets, from its description.

The catalog has no dedicated skin-type column, but the Tokopedia descriptions mention the
intended skin types ("untuk kulit berminyak", "semua jenis kulit", ...). This lets the
compare screen show a non-empty, multi-value "Target Skin Types" row.
"""
import re
from typing import List, Optional

# Phrases that mean the product is meant for every skin type.
UNIVERSAL_PATTERNS = [
    r"semua\s+jenis\s+kulit",
    r"segala\s+jenis\s+kulit",
    r"untuk\s+semua\s+kulit",
    r"all\s+skin\s+types?",
]

# Canonical order used when returning the universal set.
ALL_SKIN_TYPES = ["normal", "dry", "oily", "combination", "sensitive"]

SKIN_TYPE_PATTERNS = {
    "oily": [r"berminyak", r"\boily\b", r"kontrol\s+minyak", r"oil\s*control", r"excess\s+oil"],
    "dry": [r"\bkering\b", r"\bdry\b", r"dehidrasi", r"dehydrat", r"pelembab", r"melembabkan"],
    "sensitive": [r"sensitif", r"\bsensitive\b", r"hypoallergenic", r"anti\s*iritasi"],
    "acne-prone": [r"jerawat", r"\bacne\b", r"breakout", r"blemish", r"anti\s*acne"],
    "combination": [r"kombinasi", r"\bcombination\b"],
    "normal": [r"\bnormal\b", r"seimbang", r"balanced"],
}


def infer_suitable_skin_types(description: Optional[str]) -> List[str]:
    """Return the skin types mentioned in a product description (defaults to all)."""
    text = (description or "").lower()
    if not text:
        return []

    if any(re.search(pattern, text) for pattern in UNIVERSAL_PATTERNS):
        return list(ALL_SKIN_TYPES)

    matched = [
        skin_type
        for skin_type, patterns in SKIN_TYPE_PATTERNS.items()
        if any(re.search(pattern, text) for pattern in patterns)
    ]
    # Nothing specific mentioned: treat it as suitable for everyone.
    return matched or list(ALL_SKIN_TYPES)
