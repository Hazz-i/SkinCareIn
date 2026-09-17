# schemas/education.py
from pydantic import BaseModel, Field
from typing import List, Optional

class EducationItemSchema(BaseModel):
    id: Optional[int] = None
    title: str
    link: str
    image_url: Optional[str] = None
    snippet: Optional[str] = None
    date: Optional[str] = None
    category: Optional[str] = None

    class Config:
        from_attributes = True

class EducationListResponse(BaseModel):
    educations: List[EducationItemSchema]
    total: int
    page: int

class EducationDetailRequest(BaseModel):
    article_link: str = Field(..., description="URL of the educational article to retrieve")

class EducationDetailResponse(BaseModel):
    title: str
    author: Optional[str] = None
    date: Optional[str] = None
    cover_image: Optional[str] = None
    content_markdown: str

    class Config:
        from_attributes = True
