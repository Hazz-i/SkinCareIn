# routers/news.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.news import NewsListResponse, NewsDetailRequest, NewsDetailResponse
from services.news_service import NewsService

router = APIRouter(tags=["Skincare News"])

@router.get("", response_model=NewsListResponse, summary="Get Skincare News List (Cached)")
def get_news(page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    """Retrieve skincare news articles (served quickly from PostgreSQL cache, synchronized daily)."""
    return NewsService.get_cached_news_list(db, page=page)

@router.post("/detail", response_model=NewsDetailResponse, summary="Get Skincare News Detail (Lazy Cached)")
def get_news_detail(request: NewsDetailRequest, db: Session = Depends(get_db)):
    """Retrieve full article detail (Lazy Cache: scraped once on first access, subsequently served from database)."""
    return NewsService.get_or_scrape_news_detail(db, request.article_link)
