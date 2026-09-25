# schemas/user_skincare.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class UserSkincareCreate(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=255)
    brand: Optional[str] = Field(None, max_length=255)
    category: str = Field(..., description="One of the supported skincare step categories.")
    notes: Optional[str] = None


class UserSkincareUpdate(BaseModel):
    product_name: Optional[str] = Field(None, min_length=1, max_length=255)
    brand: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = None
    notes: Optional[str] = None


class UserSkincareResponse(BaseModel):
    id: int
    user_id: int
    product_name: str
    brand: Optional[str] = None
    category: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserSkincareListResponse(BaseModel):
    items: List[UserSkincareResponse]
    total: int


class RoutineStepSchema(BaseModel):
    step_number: int
    category: str
    label: str
    product_name: Optional[str] = None
    brand: Optional[str] = None
    tip: str = ""
    is_owned: bool = True


class DailyRoutineResponse(BaseModel):
    morning: List[RoutineStepSchema]
    night: List[RoutineStepSchema]


class CategoryOptionSchema(BaseModel):
    value: str
    label: str


class CategoryOptionsResponse(BaseModel):
    categories: List[CategoryOptionSchema]
