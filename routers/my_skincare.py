# routers/my_skincare.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.logger import log_action
from helper.routine import CATEGORY_LABELS, SKINCARE_CATEGORIES, build_daily_routine
from models.user import User
from models.user_skincare import UserSkincare
from routers.auth import get_current_user
from schemas.user_skincare import (
    CategoryOptionsResponse,
    DailyRoutineResponse,
    UserSkincareCreate,
    UserSkincareListResponse,
    UserSkincareResponse,
    UserSkincareUpdate,
)

router = APIRouter(tags=["My Skincare"])


def _validate_category(category: str) -> str:
    normalised = (category or "").strip().lower()
    if normalised not in SKINCARE_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported category '{category}'. Allowed: {', '.join(SKINCARE_CATEGORIES)}.",
        )
    return normalised


def _owned_items(db: Session, user: User) -> List[UserSkincare]:
    return (
        db.query(UserSkincare)
        .filter(UserSkincare.user_id == user.id)
        .order_by(UserSkincare.created_at.asc())
        .all()
    )


@router.get("/categories", response_model=CategoryOptionsResponse, summary="Supported Step Categories")
def list_categories():
    """Categories the client can pick from, in the canonical application order."""
    return {
        "categories": [
            {"value": value, "label": CATEGORY_LABELS.get(value, value.title())}
            for value in SKINCARE_CATEGORIES
        ]
    }


@router.get("/routine", response_model=DailyRoutineResponse, summary="Adaptive Morning & Night Routine")
def get_routine(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Builds the daily routine from the products this user owns, ordered by skincare SOP.

    Only categories the user has recorded are returned; sunscreen is morning-only and
    cleansing oil is night-only. When nothing is recorded yet the canonical order is
    returned with `is_owned=false` so the UI can still guide the user.
    """
    return build_daily_routine(_owned_items(db, user))


@router.get("", response_model=UserSkincareListResponse, summary="List My Skincare Products")
def list_my_skincare(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Every skincare product the signed-in user has added."""
    items = _owned_items(db, user)
    return {"items": items, "total": len(items)}


@router.post(
    "",
    response_model=UserSkincareResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a Skincare Product I Own",
)
def create_my_skincare(
    request: UserSkincareCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record one product the user owns, so it appears in their daily routine."""
    item = UserSkincare(
        user_id=user.id,
        product_name=request.product_name.strip(),
        brand=(request.brand or "").strip() or None,
        category=_validate_category(request.category),
        notes=(request.notes or "").strip() or None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    log_action("db", f"User {user.email} added skincare '{item.product_name}' ({item.category})")
    return item


@router.put("/{item_id}", response_model=UserSkincareResponse, summary="Update My Skincare Product")
def update_my_skincare(
    item_id: int,
    request: UserSkincareUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a product the signed-in user owns."""
    item = (
        db.query(UserSkincare)
        .filter(UserSkincare.id == item_id, UserSkincare.user_id == user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skincare product not found.")

    if request.product_name is not None:
        item.product_name = request.product_name.strip()
    if request.brand is not None:
        item.brand = request.brand.strip() or None
    if request.category is not None:
        item.category = _validate_category(request.category)
    if request.notes is not None:
        item.notes = request.notes.strip() or None

    db.commit()
    db.refresh(item)
    log_action("db", f"User {user.email} updated skincare #{item.id}")
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete My Skincare Product")
def delete_my_skincare(
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a product from the signed-in user's shelf."""
    item = (
        db.query(UserSkincare)
        .filter(UserSkincare.id == item_id, UserSkincare.user_id == user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skincare product not found.")

    db.delete(item)
    db.commit()
    log_action("db", f"User {user.email} deleted skincare #{item_id}")
    return None
