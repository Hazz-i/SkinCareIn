# routers/dashboard.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from models.user import User
from routers.auth import get_current_user
from schemas.dashboard import DashboardResponse
from services.dashboard_service import DashboardService

router = APIRouter(tags=["Personalized Dashboard"])

@router.get("", response_model=DashboardResponse, summary="Get Personalized Mobile Dashboard Data")
def get_dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve personalized user profile summary, dermatological tips, negative-filtered product recommendations, and live content previews."""
    return DashboardService.get_dashboard_data(db, user)
