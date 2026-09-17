# services/skincare_service.py
import base64
from fastapi import HTTPException, UploadFile
from helper.functions import (
    get_image_from_url, clean_extracted_text, parse_ingredients_to_list,
    get_ingredients_to_avoid, find_harmful_ingredients_with_details,
    predict_skin_type_from_image, load_resnet_skin_classifier, get_skin_type_label_mapping
)
from helper.recommendations import get_skincare_recommendations
from services.llm_service import llm_service
from core.logger import log_action

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
            raise HTTPException(status_code=400, detail="File gambar atau URL gambar diperlukan.")

        base64_str = base64.b64encode(image_bytes).decode("utf-8")
        extracted_text = await llm_service.extract_ingredients_from_image(base64_str)
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
    async def predict_skin(file: UploadFile, image_url: str):
        log_action("api", "Processing /predict-skin request")
        if file:
            image_bytes = await file.read()
        elif image_url:
            image_bytes = get_image_from_url(image_url)
        else:
            raise HTTPException(status_code=400, detail="File gambar atau URL gambar diperlukan.")

        model, transform, mapping = get_resnet()
        if model is None:
            raise HTTPException(status_code=500, detail="Model klasifikasi kulit belum tersedia.")

        prediction = predict_skin_type_from_image(image_bytes, model, transform, mapping)
        log_action("api", f"Prediction completed: {prediction.get('predicted_label')}")
        return prediction
