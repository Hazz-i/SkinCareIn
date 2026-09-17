# routers/news.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.news import NewsListResponse, NewsDetailRequest, NewsDetailResponse
from services.news_service import NewsService

router = APIRouter(tags=["Skincare News"])

@router.get("", response_model=NewsListResponse, summary="Ambil Daftar Berita Skincare (Cached)")
def get_news(page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    """Mengambil daftar berita skincare (disajikan cepat dari cache PostgreSQL yang diperbarui harian)."""
    return NewsService.get_cached_news_list(db, page=page)

@router.post("/detail", response_model=NewsDetailResponse, summary="Ambil Detail Artikel Berita (Lazy Cached)")
def get_news_detail(request: NewsDetailRequest, db: Session = Depends(get_db)):
    """Mengambil detail berita (Lazy Cache: scraping 1x saat pertama kali diakses, kunjungan berikutnya disajikan dari database)."""
    return NewsService.get_or_scrape_news_detail(db, request.article_link)
