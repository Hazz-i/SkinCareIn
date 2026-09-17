# routers/skincare.py
from fastapi import APIRouter, File, UploadFile, Form
from schemas.skincare import (
    SkinTypeEnum, ReadIngredientsResponse, PredictSkinResponse,
    RecommendationsRequest, RecommendationsResponse
)
from services.skincare_service import SkincareService
from helper.recommendations import get_skin_type_recommendations

router = APIRouter(tags=["Skincare Analysis & Recommender"])

@router.post("/read-ingredients", response_model=ReadIngredientsResponse)
async def read_ingredients(
    file: UploadFile = File(None),
    image_url: str = Form(None),
    skin_type: SkinTypeEnum = Form(...)
):
    """Scan gambar kemasan skincare untuk ekstraksi bahan via LiteLLM dan analisis keamanan"""
    return await SkincareService.analyze_ingredients(file, image_url, skin_type)

@router.post("/predict-skin", response_model=PredictSkinResponse)
async def predict_skin(
    file: UploadFile = File(None),
    image_url: str = Form(None)
):
    """Prediksi tipe kulit (dry, normal, oily) dari foto wajah via model ResNet-50"""
    return await SkincareService.predict_skin(file, image_url)

@router.post("/recommendations", response_model=RecommendationsResponse)
def get_recommendations(request: RecommendationsRequest):
    """Rekomendasi produk berdasarkan tipe kulit pengguna dari katalog database"""
    recs = get_skin_type_recommendations(request.skin_type, request.top_k)
    return {
        "recommendations": recs.get("recommendations", []),
        "total_found": recs.get("total_found", 0),
        "skin_type": request.skin_type,
        "recommendation_count": recs.get("recommendation_count", 0)
    }
