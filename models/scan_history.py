# models/scan_history.py
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from core.database import Base


class UserScanHistory(Base):
    """One recorded facial skin-type scan (from POST /skincare/predict-skin)."""

    __tablename__ = "user_scan_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    predicted_label = Column(String(50), nullable=False)
    dry = Column(Float, nullable=True)
    normal = Column(Float, nullable=True)
    oily = Column(Float, nullable=True)
    image_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
