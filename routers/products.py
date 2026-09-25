# routers/products.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import false, or_
from sqlalchemy.orm import Session

from core.database import get_db
from helper.categories import normalize_category
from helper.skin_types import infer_suitable_skin_types
from models.product import Product
from schemas.product import (
    ProductFilterOptionsResponse,
    ProductItemSchema,
    ProductListResponse,
)

router = APIRouter(tags=["Product Catalog"])


@router.get("", response_model=ProductListResponse, summary="Browse Skincare Product Catalog")
def list_products(
    search: Optional[str] = Query(None, description="Free-text match on title, brand or description."),
    brand: Optional[str] = Query(None, description="Exact brand filter."),
    type: Optional[str] = Query(None, description="Exact product type / category filter."),
    category: Optional[str] = Query(None, description="Normalised category label from /products/filters."),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Paginated skincare catalog with optional search and brand/category filters."""
    # Skip the few scraped rows with no title/type — they are unusable cards and would
    # otherwise be indistinguishable from each other in the grid.
    query = db.query(Product).filter(
        Product.title.isnot(None),
        Product.title != "",
    )

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.title.ilike(pattern),
                Product.brand.ilike(pattern),
                Product.description.ilike(pattern),
            )
        )

    if brand and brand.lower() != "all":
        query = query.filter(Product.brand.ilike(brand.strip()))

    if type and type.lower() != "all":
        query = query.filter(Product.type.ilike(type.strip()))

    if category and category.lower() != "all":
        query = _apply_category_filter(query, db, category)

    total = query.count()
    items = (
        query.order_by(Product.id.asc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "products": items,
        "total": total,
        "page": page,
        "limit": limit,
    }


def _distinct_raw_types(db: Session) -> list:
    return [
        row[0]
        for row in db.query(Product.type)
        .filter(Product.type.isnot(None), Product.type != "")
        .distinct()
        .all()
    ]


def _apply_category_filter(query, db: Session, category: str):
    """Filter by a normalised category by resolving it to the raw `type` values."""
    wanted = category.strip().lower()
    matching_types = [
        raw for raw in _distinct_raw_types(db) if normalize_category(raw).lower() == wanted
    ]
    if not matching_types:
        # No product maps to this category -> return an empty result set.
        return query.filter(false())
    return query.filter(Product.type.in_(matching_types))


@router.get("/filters", response_model=ProductFilterOptionsResponse, summary="Available Brand & Category Filters")
def get_filter_options(db: Session = Depends(get_db)):
    """Distinct brands and normalised categories that actually exist in the catalog."""
    brands = [
        row[0]
        for row in db.query(Product.brand)
        .filter(Product.brand.isnot(None), Product.brand != "")
        .distinct()
        .order_by(Product.brand.asc())
        .all()
    ]
    categories = sorted({normalize_category(raw) for raw in _distinct_raw_types(db)})
    return {"brands": brands, "categories": categories}


@router.get("/{product_id}", response_model=ProductItemSchema, summary="Get Product Detail")
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Single catalog product by id."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return ProductItemSchema.model_validate(product).model_copy(
        update={"suitable_skin_types": infer_suitable_skin_types(product.description)}
    )
