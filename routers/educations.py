# routers/educations.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.education import EducationListResponse, EducationDetailRequest, EducationDetailResponse
from services.education_service import EducationService

router = APIRouter(tags=["Skincare Educations"])

@router.get("", response_model=EducationListResponse, summary="Ambil Daftar Edukasi Skincare (Cached)")
def get_educations(page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    """Mengambil daftar topik artikel edukasi skincare (disajikan dari cache PostgreSQL yang diperbarui harian)."""
    return EducationService.get_cached_educations_list(db, page=page)

@router.post("/detail", response_model=EducationDetailResponse, summary="Ambil Detail Artikel Edukasi (Lazy Cached)")
def get_education_detail(request: EducationDetailRequest, db: Session = Depends(get_db)):
    """Mengambil detail artikel edukasi (Lazy Cache: scraping 1x saat pertama kali diakses, kunjungan berikutnya disajikan dari database)."""
    return EducationService.get_or_scrape_education_detail(db, request.article_link)
