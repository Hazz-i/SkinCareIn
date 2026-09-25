# models/user.py
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, JSON
from core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True) # Nullable for OAuth users
    
    # Profile & Demographic Information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True) # "male", "female", "other"
    
    # Dermatological Profile
    skin_type = Column(String(50), nullable=True) # "dry", "normal", "oily", "combination", "sensitive", "acne-prone"
    avoided_ingredients = Column(JSON, default=list, nullable=False) # List of prohibited ingredient strings
    
    # Security & RBAC Roles
    role = Column(String(20), default="member", nullable=False) # "member" or "admin"
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_onboarded = Column(Boolean, default=False, nullable=False)
    auth_provider = Column(String(20), default="local", nullable=False) # "local" or "google"
    
    # Verification Tokens
    verification_token = Column(String(255), nullable=True, index=True)
    verification_otp = Column(String(10), nullable=True, index=True)
    otp_expires_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __init__(self, **kwargs):
        kwargs.setdefault("role", "member")
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_verified", False)
        kwargs.setdefault("is_onboarded", False)
        kwargs.setdefault("auth_provider", "local")
        kwargs.setdefault("avoided_ingredients", [])
        super().__init__(**kwargs)
