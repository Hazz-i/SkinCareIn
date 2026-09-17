# schemas/dashboard.py
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class UserSummarySchema(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int] = None
    gender: Optional[str] = None
    skin_type: Optional[str] = None
    avoided_ingredients: List[str] = []
    is_onboarded: bool

    model_config = ConfigDict(from_attributes=True)

class DermatologicalWarningSchema(BaseModel):
    name: str
    category: str
    reason: str

class RecommendedProductSchema(BaseModel):
    id: int
    title: str
    price: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    link: Optional[str] = None
    ingredients: Optional[str] = None
    type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ContentFeedItemSchema(BaseModel):
    id: Optional[int] = None
    title: str
    link: Optional[str] = None
    image_url: Optional[str] = None
    date: Optional[str] = None
    category: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class DashboardResponse(BaseModel):
    user_summary: UserSummarySchema
    skin_health_tips: List[str]
    dermatological_warnings: List[DermatologicalWarningSchema]
    recommended_products: List[RecommendedProductSchema]
    recent_educations: List[ContentFeedItemSchema]
    recent_news: List[ContentFeedItemSchema]
