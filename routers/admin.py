# routers/admin.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from routers.auth import require_role
from services.news_service import NewsService
from services.education_service import EducationService
from core.logger import log_action

router = APIRouter(tags=["Admin Operations"])

@router.post("/sync/news", summary="Manual Sync Berita Skincare (Khusus Admin)")
def sync_news_manual(
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["admin"]))
):
    """Memicu proses scraping dan sinkronisasi artikel berita terbaru ke database PostgreSQL secara manual (Memerlukan autentikasi role `admin`)."""
    log_action("admin", f"Manual news sync triggered by admin: {admin_user.email}")
    count = NewsService.sync_news_from_source(db, max_pages=3)
    return {"status": "success", "message": f"Berhasil sinkronisasi {count} berita terbaru.", "synced_count": count}

@router.post("/sync/educations", summary="Manual Sync Edukasi Skincare (Khusus Admin)")
def sync_educations_manual(
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["admin"]))
):
    """Memicu proses scraping dan sinkronisasi artikel edukasi terbaru ke database PostgreSQL secara manual (Memerlukan autentikasi role `admin`)."""
    log_action("admin", f"Manual educations sync triggered by admin: {admin_user.email}")
    count = EducationService.sync_educations_from_source(db, max_pages=2)
    return {"status": "success", "message": f"Berhasil sinkronisasi {count} topik edukasi terbaru.", "synced_count": count}
