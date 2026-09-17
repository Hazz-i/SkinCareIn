# routers/educations.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.education import EducationListResponse, EducationDetailRequest, EducationDetailResponse
from services.education_service import EducationService

router = APIRouter(tags=["Skincare Educations"])

@router.get("", response_model=EducationListResponse, summary="Get Skincare Education List (Cached)")
def get_educations(page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    """Retrieve educational skincare topics (served from PostgreSQL cache, synchronized daily)."""
    return EducationService.get_cached_educations_list(db, page=page)

@router.post("/detail", response_model=EducationDetailResponse, summary="Get Skincare Education Detail (Lazy Cached)")
def get_education_detail(request: EducationDetailRequest, db: Session = Depends(get_db)):
    """Retrieve full educational article detail (Lazy Cache: scraped once on first access, subsequently served from database)."""
    return EducationService.get_or_scrape_education_detail(db, request.article_link)