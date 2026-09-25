# schemas/product.py
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ProductItemSchema(BaseModel):
    id: int
    # A handful of scraped rows carry a NULL title; keep the field optional so one bad row
    # can never fail the whole page (it used to return a 500 for every page containing it).
    title: Optional[str] = None
    price: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    link: Optional[str] = None
    type: Optional[str] = None
    brand: Optional[str] = None
    ingredients: Optional[str] = None
    suitable_skin_types: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    products: List[ProductItemSchema]
    total: int
    page: int
    limit: int


class ProductFilterOptionsResponse(BaseModel):
    brands: List[str]
    categories: List[str]
