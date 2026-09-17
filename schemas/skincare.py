# schemas/skincare.py
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class SkinTypeEnum(str, Enum):
    oily = "oily"
    dry = "dry"
    normal = "normal"
    acne = "acne"
    sensitive = "sensitive"

class ProductRecommendation(BaseModel):
    product_name: str
    product_image: str
    product_link: str
    price: str
    similarity_score: float = 0.0

class HarmfulIngredientDetail(BaseModel):
    name: str
    reason: str

class ReadIngredientsRecommendations(BaseModel):
    products: List[ProductRecommendation] = []
    recommendation_count: int = 0

class ReadIngredientsResponse(BaseModel):
    extracted_ingredients: List[str]
    harmful_ingredients_found: List[HarmfulIngredientDetail]
    is_safe: bool
    total_harmful_ingredients: int
    recommendations: ReadIngredientsRecommendations

class PredictSkinResponse(BaseModel):
    dry: float
    normal: float
    oily: float
    predicted_label: str

class RecommendationsRequest(BaseModel):
    skin_type: SkinTypeEnum
    top_k: int = Field(default=10, ge=1, le=20)

class SkinTypeRecommendation(BaseModel):
    product_name: str
    product_image: str
    product_link: str
    price: str
    match_reason: str

class RecommendationsResponse(BaseModel):
    recommendations: List[SkinTypeRecommendation]
    total_found: int
    skin_type: SkinTypeEnum
    recommendation_count: int
