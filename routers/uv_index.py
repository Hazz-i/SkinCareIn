# routers/uv_index.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.uv_index import UVIndexResponse
from services.uv_index_service import UVIndexService

router = APIRouter(tags=["UV Index"])

@router.get("", response_model=UVIndexResponse, summary="Get Real-time & Forecast UV Index")
def get_uv_index(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude coordinate in decimal degrees."),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude coordinate in decimal degrees."),
    timezone: str = Query("Auto", description="IANA timezone identifier (e.g. 'Asia/Jakarta'), 'UTC', or 'Auto' to infer from coordinates."),
    daily: bool = Query(True, description="Include the 5-day daily UV Index forecast."),
    hourly: bool = Query(False, description="Include the hourly UV Index forecast."),
    db: Session = Depends(get_db)
):
    """Retrieve the current UV Index, today and tomorrow maximums, and optional daily/hourly forecasts for any location (cached in PostgreSQL for 24 hours)."""
    return UVIndexService.get_uv_index(
        db,
        latitude,
        longitude,
        timezone=timezone,
        include_daily=daily,
        include_hourly=hourly
    )
