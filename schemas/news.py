# schemas/news.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class NewsItemSchema(BaseModel):
    id: Optional[int] = None
    title: str
    link: str
    image_url: Optional[str] = None
    date: Optional[str] = None
    category: Optional[str] = None

    class Config:
        from_attributes = True

class NewsListResponse(BaseModel):
    articles: List[NewsItemSchema]
    total: int
    page: int

class NewsDetailRequest(BaseModel):
    article_link: str = Field(..., description="URL berita kompas yang ingin dibuka")

class NewsDetailResponse(BaseModel):
    title: str
    cover_image: Optional[str] = None
    date: Optional[str] = None
    source: Optional[str] = None
    author: Optional[str] = None
    content_markdown: str

    class Config:
        from_attributes = True
