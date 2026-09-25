# models/user_skincare.py
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from core.database import Base


class UserSkincare(Base):
    """A skincare product the user personally owns and uses."""

    __tablename__ = "user_skincare"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_name = Column(String(255), nullable=False)
    brand = Column(String(255), nullable=True)
    # One of helper.routine.SKINCARE_CATEGORIES — drives the step order in the daily routine.
    category = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
