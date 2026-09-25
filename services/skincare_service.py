# services/skincare_service.py
import base64
from fastapi import HTTPException, UploadFile
from helper.functions import (
    get_image_from_url, clean_extracted_text, parse_ingredients_to_list,
    get_ingredients_to_avoid, find_harmful_ingredients_with_details,
    predict_skin_type_from_image, load_resnet_skin_classifier, get_skin_type_label_mapping
)
from helper.recommendations import get_skincare_recommendations
from helper.ingredients import (
    get_skin_health_tips,
    ingredients_avoid_acne,
    ingredients_avoid_dry,
    ingredients_avoid_normal,
    ingredients_avoid_oily,
    ingredients_avoid_sensitive,
)
from services.llm_service import llm_service
from core.logger import log_action

# Rule-based avoid-lists keyed by the backend skin-type vocabulary.
_AVOID_LIST_BY_SKIN_TYPE = {
    "oily": ingredients_avoid_oily,
    "dry": ingredients_avoid_dry,
    "normal": ingredients_avoid_normal,
    "acne": ingredients_avoid_acne,
    "sensitive": ingredients_avoid_sensitive,
}

# The catalog scraper stores this placeholder when a product has no ingredients.
_MISSING_INGREDIENTS_MARKER = "tidak ditemukan"

_resnet_model = None
_resnet_transform = None
_skin_label_mapping = None

def get_resnet():
    global _resnet_model, _resnet_transform, _skin_label_mapping
    if _resnet_model is None:
        try:
            _resnet_model, _resnet_transform = load_resnet_skin_classifier()
            _skin_label_mapping = get_skin_type_label_mapping()
        except Exception as e:
            log_action("api", f"Failed to load ResNet model: {e}", level="error")
    return _resnet_model, _resnet_transform, _skin_label_mapping

class SkincareService:
    @staticmethod
    async def analyze_ingredients(file: UploadFile, image_url: str, skin_type: str):
        log_action("api", f"Processing /read-ingredients for skin_type: {skin_type}")
        if file:
            image_bytes = await file.read()
        elif image_url:
            image_bytes = get_image_from_url(image_url)
        else:
            raise HTTPException(status_code=400, detail="An image file or image URL is required.")

        base64_str = base64.b64encode(image_bytes).decode("utf-8")
        try:
            extracted_text = await llm_service.extract_ingredients_from_image(base64_str)
        except Exception as e:
            message = str(e).lower()
            if "api key" in message or "authentication" in message or "api_key_invalid" in message:
                log_action("api", f"AI ingredient reader rejected the API key: {e}", level="error")
                raise HTTPException(
                    status_code=503,
                    detail="The AI ingredient reader is unavailable: the AI provider API key is invalid or missing. Please contact the administrator.",
                )
            log_action("api", f"AI ingredient reader failed: {e}", level="error")
            raise HTTPException(
                status_code=502,
                detail="The AI ingredient reader could not process the image. Please try again.",
            )

        cleaned_text = clean_extracted_text(extracted_text)

        if cleaned_text.lower() == "ingredients not found" or len(cleaned_text.split()) < 3:
            return {
                "extracted_ingredients": ["ingredients not found"],
                "harmful_ingredients_found": [],
                "is_safe": False,
                "total_harmful_ingredients": 0,
                "recommendations": {"products": [], "recommendation_count": 0}
            }

        ingredients_list = parse_ingredients_to_list(cleaned_text)
        avoid_list = get_ingredients_to_avoid(skin_type)
        harmful_found = find_harmful_ingredients_with_details(cleaned_text, avoid_list, skin_type)
        is_safe = len(harmful_found) == 0

        # Similar recommendations
        recs = get_skincare_recommendations(input_ingredients=ingredients_list, skin_type=skin_type, top_k=5)
        simplified_recs = []
        for rec in recs.get("recommendations", []):
            simplified_recs.append({
                "product_name": rec.get("product_name", "Unknown"),
                "product_image": rec.get("product_image", "Unknown"),
                "product_link": rec.get("product_link", "Unknown"),
                "price": rec.get("price", "Unknown"),
                "similarity_score": rec.get("similarity_score", 0.0)
            })

        return {
            "extracted_ingredients": ingredients_list,
            "harmful_ingredients_found": harmful_found,
            "is_safe": is_safe,
            "total_harmful_ingredients": len(harmful_found),
            "recommendations": {"products": simplified_recs, "recommendation_count": len(simplified_recs)}
        }

    @staticmethod
    def analyze_product_ingredients(ingredients_text: str, skin_type: str) -> dict:
        """Rule-based compatibility analysis of a catalog product's ingredient list."""
        skin_key = (skin_type or "normal").strip().lower()
        text = (ingredients_text or "").strip()
        log_action("api", f"Analyzing product ingredients for skin_type: {skin_key}")

        avoid_list = _AVOID_LIST_BY_SKIN_TYPE.get(skin_key, ingredients_avoid_normal)
        tips = get_skin_health_tips(skin_key)

        is_missing = (
            not text
            or len(text.split()) < 3
            or _MISSING_INGREDIENTS_MARKER in text.lower()
            or text.lower() == "ingredients not found"
        )
        if is_missing:
            return {
                "skin_type": skin_key,
                "has_ingredients": False,
                "is_safe": False,
                "safety_score": 0,
                "analyzed_ingredients": [],
                "harmful_ingredients": [],
                "tips": tips,
                "message": "This product's ingredient list is not available, so it cannot be analysed yet.",
            }

        ingredients_list = parse_ingredients_to_list(text)
        harmful_found = find_harmful_ingredients_with_details(text, avoid_list, skin_key)

        analyzed_ingredients = []
        for name in ingredients_list:
            lower_name = name.lower()
            match = next(
                (
                    item
                    for item in harmful_found
                    if item["name"].lower() in lower_name or lower_name in item["name"].lower()
                ),
                None,
            )
            analyzed_ingredients.append({
                "name": name,
                "rating": "caution" if match else "safe",
                "purpose": (match or {}).get("reason") or "Commonly well-tolerated ingredient.",
            })

        safety_score = max(40, 100 - 15 * len(harmful_found))
        return {
            "skin_type": skin_key,
            "has_ingredients": True,
            "is_safe": len(harmful_found) == 0,
            "safety_score": safety_score,
            "analyzed_ingredients": analyzed_ingredients,
            "harmful_ingredients": harmful_found,
            "tips": tips,
            "message": None,
        }

    @staticmethod
    async def predict_skin(file: UploadFile, image_url: str):
        log_action("api", "Processing /predict-skin request")
        if file:
            image_bytes = await file.read()
        elif image_url:
            image_bytes = get_image_from_url(image_url)
        else:
            raise HTTPException(status_code=400, detail="An image file or image URL is required.")

        model, transform, mapping = get_resnet()
        if model is None:
            raise HTTPException(status_code=500, detail="The skin classification model is not available yet.")

        prediction = predict_skin_type_from_image(image_bytes, model, transform, mapping)
        log_action("api", f"Prediction completed: {prediction.get('predicted_label')}")
        return prediction
