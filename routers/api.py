# routers/api.py
from fastapi import APIRouter
from routers.auth import router as auth_router
from routers.skincare import router as skincare_router
from routers.news import router as news_router
from routers.educations import router as educations_router
from routers.admin import router as admin_router
from core.config import settings

api_router = APIRouter()

@api_router.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(skincare_router, prefix="/skincare")
api_router.include_router(news_router, prefix="/news")
api_router.include_router(educations_router, prefix="/educations")
api_router.include_router(admin_router, prefix="/admin")
