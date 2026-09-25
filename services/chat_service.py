# services/chat_service.py
"""In-app assistant.

Two guardrails keep it from making things up:

1. The system prompt hard-limits the assistant to SkinSight topics and tells it to refuse
   anything else.
2. Every product question is grounded in rows pulled from the `products` table — the exact
   same catalog the app shows. The model is told the injected block is its only source of
   product truth, and to admit when something is not in the catalog.
"""
import re
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.logger import log_action
from models.product import Product
from models.user import User
from schemas.chat import ChatRequest
from services.llm_service import llm_service

MAX_PRODUCTS = 5

# Words that carry no retrieval signal on their own.
_STOPWORDS = {
    "yang", "dan", "atau", "untuk", "dengan", "dari", "pada", "itu", "ini", "apa", "apakah",
    "ada", "adalah", "bagaimana", "gimana", "kenapa", "mengapa", "bisa", "boleh", "tolong",
    "saya", "aku", "kamu", "nya", "juga", "saja", "aja", "tidak", "bukan", "kalau", "jika",
    "biar", "supaya", "sih", "dong", "ya", "kak", "min", "produk", "produknya", "skincare",
    "rekomendasi", "rekomendasiin", "cari", "carikan", "kasih", "minta", "tolong", "bagus",
    "cocok", "kulit", "wajah", "the", "and", "for", "with", "what", "which", "good", "best",
    "product", "products", "recommend", "recommendation", "skin", "please", "show", "about",
    "siapa", "kapan", "dimana", "kemana", "berapa", "sekarang", "sebenarnya", "menurut",
}

# Phrases that mean "give me a product suggestion" even without naming a product.
# Indonesian words are kept so the matcher still works if a user writes in Indonesian.
_RECOMMENDATION_INTENT = {
    # Indonesian
    "rekomendasi", "rekomen", "rekomendasikan", "saran", "sarankan", "cocok", "bagus",
    "terbaik", "cari", "carikan", "produk", "pelembab", "sabun", "masker", "acne",
    # English
    "recommend", "recommends", "recommended", "recommendation", "recommendations",
    "suggest", "suggestion", "suggestions", "best", "top", "options", "product",
    "products", "skincare", "sunscreen", "toner", "serum", "moisturizer", "moisturiser",
    "cleanser", "mask", "treatment", "acne", "routine",
}

# Words that mean the user is asking about a specific product's details.
_PRODUCT_DETAIL_WORDS = {
    "harga", "harganya", "price", "pricing", "cost", "bahan", "kandungan", "ingredient",
    "ingredients", "beli", "buy", "purchase", "link", "checkout", "stok", "stock", "promo",
    "diskon", "discount", "ukuran", "size", "review", "reviews", "ulasan",
}

# Maps common complaints onto the catalog's own skin-type vocabulary.
_SKIN_TYPE_HINTS: Dict[str, List[str]] = {
    "oily": ["berminyak", "oily", "kontrol minyak", "oil control", "sebum"],
    "dry": ["kering", "dry", "dehidrasi", "melembabkan", "pelembab", "hidrasi"],
    "sensitive": ["sensitif", "sensitive", "hypoallergenic", "iritasi"],
    "acne": ["jerawat", "acne", "breakout", "blemish", "komedo"],
    "combination": ["kombinasi", "combination"],
    "normal": ["normal", "semua jenis kulit", "all skin types"],
}

_PROJECT_CONTEXT = """
SkinSight is an AI-powered skincare companion app. Features available in the app:
- Face Scan ("AI Skin Scanner"): photograph your face and a classification model predicts your skin type (dry / normal / oily); the result can be saved to your profile.
- Ingredient Scan: photograph or import a photo of a product's ingredient label, then the app extracts the ingredient list and flags the ones risky for the user's skin type.
- Products: the real skincare catalog, filterable by brand and category, with a detail page, ingredient safety analysis, and side-by-side comparison of two products.
- Home: a real-time UV Index card based on the user's location, a daily routine checklist (morning/night), and product recommendations.
- Explore: skincare news and educational articles.
- Profile: skin data and date of birth, face scan history, favourites, and "My Skincare" for the products the user owns (used to build their routine).
- This chat assistant answers only about the SkinSight app and skincare.
""".strip()


def _extract_keywords(text: str) -> List[str]:
    """Meaningful words from the user's message, used to query the catalog."""
    tokens = re.findall(r"[a-zA-Z0-9]+", (text or "").lower())
    seen: List[str] = []
    for token in tokens:
        if len(token) < 4 or token in _STOPWORDS or token.isdigit():
            continue
        if token not in seen:
            seen.append(token)
    return seen


def _detect_skin_type(text: str) -> Optional[str]:
    lowered = (text or "").lower()
    for skin_type, hints in _SKIN_TYPE_HINTS.items():
        if any(hint in lowered for hint in hints):
            # "normal" is a very loose hint, so only use it when nothing else matched.
            if skin_type == "normal":
                continue
            return skin_type
    return None


def _wants_recommendation(text: str) -> bool:
    """True when the message is actually asking for product suggestions."""
    tokens = set(re.findall(r"[a-zA-Z0-9]+", (text or "").lower()))
    return bool(tokens & _RECOMMENDATION_INTENT)


def _asks_about_product_details(text: str) -> bool:
    """True when the message asks about a specific product's price/ingredients/link."""
    tokens = set(re.findall(r"[a-zA-Z0-9]+", (text or "").lower()))
    return bool(tokens & _PRODUCT_DETAIL_WORDS)


def _filter_by_keywords(query, keywords: List[str], include_description: bool):
    conditions = []
    for keyword in keywords[:6]:
        pattern = f"%{keyword}%"
        conditions.append(Product.title.ilike(pattern))
        conditions.append(Product.brand.ilike(pattern))
        conditions.append(Product.type.ilike(pattern))
        if include_description:
            conditions.append(Product.description.ilike(pattern))
    return query.filter(or_(*conditions))


def _search_products(
    db: Session,
    keywords: List[str],
    allow_description: bool,
    limit: int = MAX_PRODUCTS,
) -> List[Product]:
    """Look the keywords up in the catalog.

    Titles/brands/categories are tried first. Descriptions are long and full of generic
    words ("Indonesia", "BPOM", ...), so they are only consulted for messages that actually
    look like a product/skincare question — otherwise an off-topic question would drag in
    unrelated rows.
    """
    if not keywords:
        return []

    base = db.query(Product).filter(Product.title.isnot(None), Product.title != "")
    matches = (
        _filter_by_keywords(base, keywords, include_description=False)
        .order_by(Product.id.asc())
        .limit(limit)
        .all()
    )
    if matches or not allow_description:
        return matches

    return (
        _filter_by_keywords(base, keywords, include_description=True)
        .order_by(Product.id.asc())
        .limit(limit)
        .all()
    )


def _search_by_brand(db: Session, keywords: List[str], limit: int = MAX_PRODUCTS) -> List[Product]:
    """Brand-only lookup used as the "is the user talking about a product?" signal.

    Deliberately narrow: matching titles on a shared ingredient word (e.g. "niacinamide")
    would make a general skincare question look like a product question.
    """
    if not keywords:
        return []

    conditions = [Product.brand.ilike(f"%{keyword}%") for keyword in keywords[:6]]
    return (
        db.query(Product)
        .filter(Product.title.isnot(None), Product.title != "")
        .filter(or_(*conditions))
        .order_by(Product.id.asc())
        .limit(limit)
        .all()
    )


def _search_by_skin_type(db: Session, skin_type: str, limit: int = MAX_PRODUCTS) -> List[Product]:
    """Fallback when the user asks for a recommendation without naming a product."""
    hints = _SKIN_TYPE_HINTS.get(skin_type, [])
    if not hints:
        return []

    conditions = []
    for hint in hints:
        pattern = f"%{hint}%"
        conditions.append(Product.title.ilike(pattern))
        conditions.append(Product.description.ilike(pattern))

    return (
        db.query(Product)
        .filter(Product.title.isnot(None), Product.title != "")
        .filter(or_(*conditions))
        .order_by(Product.id.asc())
        .limit(limit)
        .all()
    )


def _clean(value: Optional[str], fallback: str = "-") -> str:
    text = str(value or "").strip()
    if not text or text.lower() in ("none", "nan"):
        return fallback
    return text


def _catalog_block(products: List[Product]) -> str:
    if not products:
        return "PRODUCT CATALOG: (no catalog product matched this question)"

    lines = ["PRODUCT CATALOG (real rows from the SkinSight database):"]
    for index, product in enumerate(products, start=1):
        ingredients = _clean(product.ingredients)
        if len(ingredients) > 180:
            ingredients = ingredients[:180] + "…"
        lines.append(
            f"[{index}] {_clean(product.title)}\n"
            f"    brand: {_clean(product.brand)} | category: {_clean(product.type)} | price: {_clean(product.price)}\n"
            f"    ingredients: {ingredients}\n"
            f"    link: {_clean(product.link)}"
        )
    return "\n".join(lines)


def _build_system_prompt(user: User, products: List[Product]) -> str:
    profile = [
        f"- skin type: {_clean(user.skin_type, 'not set')}",
        f"- gender: {_clean(user.gender, 'not set')}",
    ]
    if user.avoided_ingredients:
        profile.append(f"- ingredients to avoid: {', '.join(user.avoided_ingredients[:10])}")

    return f"""You are the "SkinSight Assistant", the official chatbot inside the SkinSight app.

HARD RULES (never break these):
1. Answer ONLY questions about the SkinSight app, its features, how to use them, skincare,
   active ingredients, skin types, and the products in the PRODUCT CATALOG block below.
2. If a question is off-topic (politics, general news, coding, maths, small talk, ...), politely
   decline in one sentence and steer back to skincare/SkinSight. Do NOT answer the off-topic
   question itself.
3. For PRODUCT questions (name, price, brand, ingredients, link, suitability) use ONLY the data in
   the PRODUCT CATALOG block below. NEVER invent a product, price, brand or link. If the product
   asked about is not in the catalog, say honestly that it is not in the SkinSight catalog, then
   offer a similar product that really is in the catalog.
4. Never claim you can do something the app cannot (e.g. process payments, edit account data,
   send emails).
5. Writing style:
   - Friendly and warm, like a friend who knows skincare. Use "I" and "you".
   - ALWAYS answer in English, even if the user writes in another language.
   - NEVER draw horizontal divider lines between sections.
   - Use simple markdown only: **bold** for key points, a hash at the start of a line for a
     section heading when it helps, and a dash at the start of a line for lists. No tables.
   - Get to the point in roughly 120 words or fewer, no filler.
   - The app itself is personalised: refer to the user's own skin profile when relevant.
6. Keep casual conversation short. Only talk about catalog products when the user actually asks
   about products or asks for a recommendation — do not volunteer a product list otherwise.
7. If you do not have enough data, say you do not know — never guess.

APP CONTEXT:
{_PROJECT_CONTEXT}

USER PROFILE:
{chr(10).join(profile)}

{_catalog_block(products)}"""


class ChatService:
    @staticmethod
    def _select_products(db: Session, messages, user: User) -> List[Product]:
        """Catalog rows that ground this turn. Empty list means a plain chat turn.

        An empty result is intentional for small talk and pure skincare theory: the catalog is
        only injected (and returned to the client) when the user asks about products or asks
        for a recommendation.
        """
        user_messages = [m.content for m in messages if m.role == "user"]
        last_message = user_messages[-1] if user_messages else ""
        # Include the previous question so short follow-ups ("how much is it?") still
        # resolve against the product asked about one turn earlier.
        search_text = " ".join(user_messages[-2:])
        keywords = _extract_keywords(search_text)

        # Naming a brand that exists in the catalog is the strongest product signal.
        brand_hits = _search_by_brand(db, keywords)
        asks_about_products = _wants_recommendation(search_text) or _asks_about_product_details(
            last_message
        )

        if not (brand_hits or asks_about_products):
            return []

        products = _search_products(
            db, keywords, allow_description=asks_about_products
        ) or brand_hits
        if products:
            return products

        skin_type = _detect_skin_type(search_text) or (user.skin_type or "").strip().lower()
        return _search_by_skin_type(db, skin_type) if skin_type else []

    @staticmethod
    async def reply(db: Session, user: User, payload: ChatRequest) -> dict:
        history = [{"role": m.role, "content": m.content} for m in payload.messages]

        products = ChatService._select_products(db, payload.messages, user)
        system_prompt = _build_system_prompt(user, products)
        log_action(
            "llm",
            f"Assistant grounded with {len(products)} catalog product(s) for user {user.email}",
        )

        try:
            reply_text = await llm_service.chat_completion(history, system_prompt)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The assistant is unavailable right now. Please try again in a moment.",
            )

        if not reply_text:
            reply_text = "Sorry, I could not answer that. Try asking something else about skincare or the SkinSight app."

        return {
            "reply": reply_text,
            "grounded": bool(products),
            "products": [
                {
                    "id": product.id,
                    "name": _clean(product.title, "Produk"),
                    "brand": product.brand,
                    "category": product.type,
                    "price": product.price,
                    "image_url": product.image_url,
                    "link": product.link,
                }
                for product in products
            ],
        }
