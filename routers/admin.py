# routers/admin.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from routers.auth import require_role
from services.news_service import NewsService
from services.education_service import EducationService
from core.logger import log_action

router = APIRouter(tags=["Admin Operations"])

@router.post("/sync/news", summary="Manual Sync News Articles (Admin Only)")
def sync_news_manual(
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["admin"]))
):
    """Trigger manual scraping and synchronization of latest skincare news articles to PostgreSQL database (Requires 'admin' role)."""
    log_action("admin", f"Manual news sync triggered by admin: {admin_user.email}")
    count = NewsService.sync_news_from_source(db, max_pages=5, until_exhausted=True)
    return {"status": "success", "message": f"Successfully synchronized {count} latest news articles.", "synced_count": count}

@router.post("/sync/educations", summary="Manual Sync Education Topics (Admin Only)")
def sync_educations_manual(
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["admin"]))
):
    """Trigger manual scraping and synchronization of latest skincare education topics to PostgreSQL database (Requires 'admin' role)."""
    log_action("admin", f"Manual educations sync triggered by admin: {admin_user.email}")
    count = EducationService.sync_educations_from_source(db, max_pages=5, until_exhausted=True)
    return {"status": "success", "message": f"Successfully synchronized {count} latest education topics.", "synced_count": count}
