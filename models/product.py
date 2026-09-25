# models/product.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from core.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    price = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    link = Column(Text, nullable=True)
    ingredients = Column(Text, nullable=True)
    type = Column(String(100), nullable=True)
    brand = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
