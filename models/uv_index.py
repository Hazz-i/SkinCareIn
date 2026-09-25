# models/uv_index.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, UniqueConstraint
from datetime import datetime
from core.database import Base

class UVIndexCache(Base):
    __tablename__ = "uv_index_cache"
    __table_args__ = (
        UniqueConstraint("latitude", "longitude", "timezone", name="uq_uv_index_location"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    timezone = Column(String(100), default="Auto", nullable=False)
    payload = Column(Text, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
