# services/auth_service.py
import secrets
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.user import User
from schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    VerifyOTPRequest,
    ResendVerificationRequest,
    OnboardingRequest,
    UpdateProfileRequest
)
from services.email_service import EmailService
from core.security import hash_password, verify_password, create_access_token
from core.logger import log_action

class AuthService:
    @staticmethod
    def register_user(db: Session, request: UserRegisterRequest) -> dict:
        """Register a new member with 6-digit OTP and email verification link."""
        if db.query(User).filter(User.email == request.email).first():
            log_action("auth", f"Registration failed: email {request.email} already registered", level="warning")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered.")
        
        if db.query(User).filter(User.username == request.username).first():
            log_action("auth", f"Registration failed: username {request.username} already taken", level="warning")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is already taken.")
        
        assigned_role = "admin" if request.role == "admin" else "member"
        verification_token = secrets.token_urlsafe(32)
        verification_otp = f"{random.randint(0, 999999):06d}"
        otp_expires_at = datetime.utcnow() + timedelta(minutes=15)

        new_user = User(
            email=request.email,
            username=request.username,
            hashed_password=hash_password(request.password),
            role=assigned_role,
            is_active=True,
            is_verified=False,
            is_onboarded=False,
            auth_provider="local",
            verification_token=verification_token,
            verification_otp=verification_otp,
            otp_expires_at=otp_expires_at
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Dispatch verification email (with console fallback)
        EmailService.send_verification_email(new_user.email, verification_token, verification_otp)

        log_action("auth", f"User registered successfully: {new_user.email} (role: {new_user.role}, unverified)")
        return {
            "message": "Registration successful. Please verify your email with the 6-digit code or link sent to your inbox.",
            "email": new_user.email,
            "is_verified": False
        }

    @staticmethod
    def verify_email(db: Session, token: str) -> dict:
        """Verify user email via URL verification token."""
        if not token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token is required.")

        user = db.query(User).filter(User.verification_token == token).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token.")

        user.is_verified = True
        user.verification_token = None
        user.verification_otp = None
        user.otp_expires_at = None
        db.commit()

        log_action("auth", f"Email verified via link for user: {user.email}")
        return {
            "message": "Email successfully verified. You can now log in to your account.",
            "email": user.email,
            "is_verified": True
        }

    @staticmethod
    def verify_otp(db: Session, request: VerifyOTPRequest) -> dict:
        """Verify user email via 6-digit numeric OTP code."""
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        if user.is_verified:
            return {
                "message": "Email is already verified.",
                "email": user.email,
                "is_verified": True
            }

        if not user.verification_otp or user.verification_otp != request.otp:
            log_action("auth", f"Invalid OTP attempt for {request.email}", level="warning")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code.")

        if user.otp_expires_at and user.otp_expires_at < datetime.utcnow():
            log_action("auth", f"Expired OTP attempt for {request.email}", level="warning")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code has expired. Please request a new code.")

        user.is_verified = True
        user.verification_token = None
        user.verification_otp = None
        user.otp_expires_at = None
        db.commit()

        log_action("auth", f"Email verified via OTP for user: {user.email}")
        return {
            "message": "Email successfully verified. You can now log in to your account.",
            "email": user.email,
            "is_verified": True
        }

    @staticmethod
    def resend_verification(db: Session, request: ResendVerificationRequest) -> dict:
        """Regenerate and resend verification code and link."""
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        if user.is_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already verified.")

        verification_token = secrets.token_urlsafe(32)
        verification_otp = f"{random.randint(0, 999999):06d}"
        otp_expires_at = datetime.utcnow() + timedelta(minutes=15)

        user.verification_token = verification_token
        user.verification_otp = verification_otp
        user.otp_expires_at = otp_expires_at
        db.commit()

        EmailService.send_verification_email(user.email, verification_token, verification_otp)
        log_action("auth", f"Verification code resent to {user.email}")

        return {
            "message": "Verification code resent successfully. Please check your inbox.",
            "email": user.email
        }

    @staticmethod
    def authenticate_user(db: Session, request: UserLoginRequest) -> dict:
        """Authenticate user credentials and enforce email verification gate."""
        user = db.query(User).filter(User.email == request.email).first()
        if not user or not user.hashed_password or not verify_password(request.password, user.hashed_password):
            log_action("auth", f"Invalid login credentials for email: {request.email}", level="warning")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
        
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive.")
        
        # Enforce email verification gate
        if not user.is_verified:
            log_action("auth", f"Login blocked - unverified email: {user.email}", level="warning")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified. Please verify your email using the OTP code sent to your inbox."
            )
        
        token = create_access_token(data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "is_onboarded": user.is_onboarded
        })
        log_action("auth", f"User logged in successfully: {user.email} (role: {user.role}, onboarded: {user.is_onboarded})")
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": user.role,
            "is_onboarded": user.is_onboarded
        }

    @staticmethod
    def complete_onboarding(db: Session, user: User, request: OnboardingRequest) -> User:
        """Save onboarding dermatological attributes and mark user as onboarded."""
        user.first_name = request.first_name
        user.last_name = request.last_name
        user.age = request.age
        user.gender = request.gender
        user.skin_type = request.skin_type
        user.avoided_ingredients = request.avoided_ingredients
        user.is_onboarded = True

        db.commit()
        db.refresh(user)
        log_action("auth", f"Onboarding completed for user {user.email}: skin_type={user.skin_type}")
        return user

    @staticmethod
    def update_profile(db: Session, user: User, request: UpdateProfileRequest) -> User:
        """Update user profile and dermatological preferences."""
        if request.first_name is not None:
            user.first_name = request.first_name
        if request.last_name is not None:
            user.last_name = request.last_name
        if request.age is not None:
            user.age = request.age
        if request.gender is not None:
            user.gender = request.gender
        if request.skin_type is not None:
            user.skin_type = request.skin_type
        if request.avoided_ingredients is not None:
            user.avoided_ingredients = request.avoided_ingredients

        db.commit()
        db.refresh(user)
        log_action("auth", f"Profile updated for user {user.email}")
        return user
