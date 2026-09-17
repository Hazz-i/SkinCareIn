# routers/skincare.py
from fastapi import APIRouter, File, UploadFile, Form, Query
from schemas.skincare import (
    SkinTypeEnum, ReadIngredientsResponse, PredictSkinResponse,
    RecommendationsRequest, RecommendationsResponse
)
from services.skincare_service import SkincareService
from helper.recommendations import get_skin_type_recommendations
from helper.ingredients import get_avoided_ingredients_for_skin, get_skin_health_tips

router = APIRouter(tags=["Skincare Analysis & Recommender"])

@router.post("/read-ingredients", response_model=ReadIngredientsResponse, summary="Analyze Skincare Ingredients (LiteLLM)")
async def read_ingredients(
    file: UploadFile = File(None),
    image_url: str = Form(None),
    skin_type: SkinTypeEnum = Form(...)
):
    """Scan product packaging image to extract ingredients via LiteLLM and analyze safety compatibility."""
    return await SkincareService.analyze_ingredients(file, image_url, skin_type)

@router.post("/predict-skin", response_model=PredictSkinResponse, summary="Predict Facial Skin Type (ResNet-50)")
async def predict_skin(
    file: UploadFile = File(None),
    image_url: str = Form(None)
):
    """Predict skin type (dry, normal, oily) from facial photograph using ResNet-50 deep learning model."""
    return await SkincareService.predict_skin(file, image_url)

@router.post("/recommendations", response_model=RecommendationsResponse, summary="Product Recommendations by Skin Type")
def get_recommendations(request: RecommendationsRequest):
    """Retrieve personalized product recommendations matching user's skin type from database catalog."""
    recs = get_skin_type_recommendations(request.skin_type, request.top_k)
    return {
        "recommendations": recs.get("recommendations", []),
        "total_found": recs.get("total_found", 0),
        "skin_type": request.skin_type,
        "recommendation_count": recs.get("recommendation_count", 0)
    }

@router.get("/ingredients-to-avoid", summary="Get Prohibited Ingredients & Care Tips by Skin Type")
def get_ingredients_to_avoid(
    skin_type: str = Query(..., description="Skin classification (sensitive, oily, dry, combination, acne-prone, normal)")
):
    """Retrieve curated prohibited cosmetic ingredients and clinical tips tailored for specific skin types."""
    return {
        "skin_type": skin_type,
        "exceptions": get_avoided_ingredients_for_skin(skin_type),
        "tips": get_skin_health_tips(skin_type)
    }
