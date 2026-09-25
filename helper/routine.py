# helper/routine.py
"""Builds the daily skincare routine from what the user actually owns.

Order follows standard skincare practice (thinnest → thickest consistency):
  Morning: cleanse -> tone -> treat (serum) -> moisturise -> protect (SPF)
  Night:   oil cleanse -> water cleanse -> tone -> treat -> moisturise
Sunscreen only belongs to the morning; cleansing oil only to the night.
"""
from typing import Dict, List

SKINCARE_CATEGORIES = [
    "oil-cleanser",
    "cleanser",
    "toner",
    "essence",
    "serum",
    "treatment",
    "eye-cream",
    "moisturizer",
    "sunscreen",
    "exfoliator",
    "mask",
]

MORNING_SEQUENCE = ["cleanser", "toner", "essence", "serum", "treatment", "eye-cream", "moisturizer", "sunscreen"]
NIGHT_SEQUENCE = ["oil-cleanser", "cleanser", "toner", "essence", "serum", "treatment", "eye-cream", "moisturizer"]

# Shown when the user has nothing recorded yet, so the screen still explains the order.
DEFAULT_MORNING = ["cleanser", "toner", "serum", "moisturizer", "sunscreen"]
DEFAULT_NIGHT = ["oil-cleanser", "cleanser", "toner", "treatment", "moisturizer"]

CATEGORY_LABELS = {
    "oil-cleanser": "Oil Cleanser",
    "cleanser": "Facial Cleanser",
    "toner": "Toner",
    "essence": "Essence",
    "serum": "Serum",
    "treatment": "Treatment / Active",
    "eye-cream": "Eye Cream",
    "moisturizer": "Moisturizer",
    "sunscreen": "Sunscreen",
    "exfoliator": "Exfoliator",
    "mask": "Mask",
}

CATEGORY_TIPS = {
    "oil-cleanser": "Melt away sunscreen and makeup before your water-based cleanser.",
    "cleanser": "Use a gentle, low-pH cleanser so the barrier stays intact.",
    "toner": "Rehydrate and prep the skin so actives absorb evenly.",
    "essence": "Light hydration layer that boosts the steps after it.",
    "serum": "Apply onto damp skin for better absorption.",
    "treatment": "Actives like retinol go at night only; start 2-3x a week.",
    "eye-cream": "Pat gently around the orbital bone, never drag.",
    "moisturizer": "Seal in everything applied before it.",
    "sunscreen": "Two finger-lengths, and reapply every 2 hours outdoors.",
    "exfoliator": "1-2x a week at night is plenty for most skin.",
    "mask": "Follow the label timing, then moisturise after.",
}


def _build(owned: Dict[str, List[dict]], sequence: List[str], fallback: List[str]) -> List[dict]:
    """Order the user's products by `sequence`; fall back to placeholder steps when empty."""
    steps: List[dict] = []
    step_number = 0

    for category in sequence:
        products = owned.get(category, [])
        if not products:
            continue
        step_number += 1
        primary = products[0]
        steps.append(
            {
                "step_number": step_number,
                "category": category,
                "label": CATEGORY_LABELS.get(category, category.title()),
                "product_name": primary.get("product_name"),
                "brand": primary.get("brand"),
                "tip": CATEGORY_TIPS.get(category, ""),
                "is_owned": True,
            }
        )

    if steps:
        return steps

    # Nothing recorded yet — return the canonical order as guidance.
    for index, category in enumerate(fallback, start=1):
        steps.append(
            {
                "step_number": index,
                "category": category,
                "label": CATEGORY_LABELS.get(category, category.title()),
                "product_name": None,
                "brand": None,
                "tip": CATEGORY_TIPS.get(category, ""),
                "is_owned": False,
            }
        )
    return steps


def build_daily_routine(items: List[object]) -> Dict[str, List[dict]]:
    """Group the user's owned products by category and order them per the AM/PM SOP."""
    owned: Dict[str, List[dict]] = {}
    for item in items:
        category = getattr(item, "category", None)
        if category not in SKINCARE_CATEGORIES:
            continue
        owned.setdefault(category, []).append(
            {
                "product_name": getattr(item, "product_name", None),
                "brand": getattr(item, "brand", None),
            }
        )

    return {
        "morning": _build(owned, MORNING_SEQUENCE, DEFAULT_MORNING),
        "night": _build(owned, NIGHT_SEQUENCE, DEFAULT_NIGHT),
    }
