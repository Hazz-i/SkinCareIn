# schemas/auth.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserRegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: Optional[str] = "member" # 'admin' or 'member'

class UserRegisterResponse(BaseModel):
    message: str
    email: str
    is_verified: bool

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    is_onboarded: bool = False

class OnboardingRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    age: int = Field(..., ge=10, le=120)
    gender: str = Field(..., pattern="^(male|female|other)$")
    skin_type: str = Field(..., pattern="^(dry|normal|oily|combination|sensitive|acne-prone)$")
    avoided_ingredients: List[str] = Field(default_factory=list, max_length=50)

class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    age: Optional[int] = Field(None, ge=10, le=120)
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    skin_type: Optional[str] = Field(None, pattern="^(dry|normal|oily|combination|sensitive|acne-prone)$")
    avoided_ingredients: Optional[List[str]] = None

class UserProfileResponse(BaseModel):
    id: int
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    skin_type: Optional[str] = None
    avoided_ingredients: List[str] = []
    role: str
    is_active: bool
    is_verified: bool
    is_onboarded: bool
    auth_provider: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
