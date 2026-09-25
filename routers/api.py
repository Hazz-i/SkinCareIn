# routers/api.py
from fastapi import APIRouter
from routers.auth import router as auth_router
from routers.skincare import router as skincare_router
from routers.news import router as news_router
from routers.educations import router as educations_router
from routers.uv_index import router as uv_index_router
from routers.products import router as products_router
from routers.my_skincare import router as my_skincare_router
from routers.scan_history import router as scan_history_router
from routers.admin import router as admin_router
from routers.dashboard import router as dashboard_router
from routers.chat import router as chat_router
from core.config import settings

api_router = APIRouter()

@api_router.get("/health", tags=["Health"], summary="Health Check Service")
def health_check():
    """Check backend service operational status and release version."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(dashboard_router, prefix="/dashboard")
api_router.include_router(skincare_router, prefix="/skincare")
api_router.include_router(news_router, prefix="/news")
api_router.include_router(educations_router, prefix="/educations")
api_router.include_router(uv_index_router, prefix="/uv-index")
api_router.include_router(products_router, prefix="/products")
api_router.include_router(my_skincare_router, prefix="/my-skincare")
api_router.include_router(scan_history_router, prefix="/my-scan-history")
api_router.include_router(admin_router, prefix="/admin")
api_router.include_router(chat_router, prefix="/chat")
