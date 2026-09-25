# routers/scan_history.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.logger import log_action
from models.scan_history import UserScanHistory
from models.user import User
from routers.auth import get_current_user
from schemas.scan_history import (
    ScanHistoryCreate,
    ScanHistoryListResponse,
    ScanHistoryResponse,
)

router = APIRouter(tags=["Face Scan History"])


@router.get("", response_model=ScanHistoryListResponse, summary="My Face Scan History")
def list_my_scans(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Every facial scan this user has run, newest first, plus the total count."""
    query = (
        db.query(UserScanHistory)
        .filter(UserScanHistory.user_id == user.id)
        .order_by(UserScanHistory.created_at.desc())
    )
    items = query.limit(limit).all()
    return {"items": items, "total": query.count(), "latest": items[0] if items else None}


@router.post(
    "",
    response_model=ScanHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a Face Scan",
)
def record_scan(
    request: ScanHistoryCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Persist the result of a completed skin-type scan so it shows up in history."""
    entry = UserScanHistory(
        user_id=user.id,
        predicted_label=request.predicted_label,
        dry=request.dry,
        normal=request.normal,
        oily=request.oily,
        image_url=request.image_url,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    log_action("db", f"User {user.email} recorded scan #{entry.id} ({entry.predicted_label})")
    return entry


@router.delete(
    "/{scan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Face Scan",
)
def delete_scan(
    scan_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove one scan from the signed-in user's history."""
    entry = (
        db.query(UserScanHistory)
        .filter(UserScanHistory.id == scan_id, UserScanHistory.user_id == user.id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")

    db.delete(entry)
    db.commit()
    log_action("db", f"User {user.email} deleted scan #{scan_id}")
    return None
