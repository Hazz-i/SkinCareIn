# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import security_bearer, decode_access_token
from models.user import User
from schemas.auth import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    TokenResponse,
    UserProfileResponse,
    VerifyOTPRequest,
    ResendVerificationRequest,
    OnboardingRequest,
    UpdateProfileRequest,
    ForgotPasswordRequest,
    ResetOTPRequest,
    ResetPasswordRequest,
    ResetTokenResponse,
    MessageResponse
)
from services.auth_service import AuthService
from core.logger import log_action

router = APIRouter(tags=["Authentication"])

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please include a Bearer token in the Authorization header.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user

def require_role(allowed_roles: list):
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            log_action("auth", f"Unauthorized role access: user {user.email} with role {user.role} attempted {allowed_roles}", level="warning")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: insufficient role permissions.")
        return user
    return role_checker

@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED, summary="Register New User")
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new member account and send verification code/link to email."""
    return AuthService.register_user(db, request)

@router.post("/login", response_model=TokenResponse, summary="User Login & Obtain JWT Access Token")
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate user credentials and obtain JWT access token. Requires verified email."""
    return AuthService.authenticate_user(db, request)

@router.get("/verify-email", summary="Verify Email via Token Link")
def verify_email(
    token: str = Query(..., description="Cryptographic verification token sent via email link"),
    db: Session = Depends(get_db)
):
    """Verify user email address using clickable link token."""
    return AuthService.verify_email(db, token)

@router.post("/verify-otp", summary="Verify Email via 6-Digit OTP Code")
def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verify user email address using 6-digit numeric OTP code for mobile applications."""
    return AuthService.verify_otp(db, request)

@router.post("/resend-verification", summary="Resend Verification Code & Link")
def resend_verification(request: ResendVerificationRequest, db: Session = Depends(get_db)):
    """Generate fresh OTP code and verification link, and resend verification email."""
    return AuthService.resend_verification(db, request)

@router.post("/onboarding", response_model=UserProfileResponse, summary="Complete Post-Login Onboarding")
def onboarding(
    request: OnboardingRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit user dermatological profile (skin type, age, gender, avoided ingredients) and complete onboarding."""
    return AuthService.complete_onboarding(db, user, request)

@router.put("/profile", response_model=UserProfileResponse, summary="Update User Profile & Preferences")
def update_profile(
    request: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user identity and dermatological preferences."""
    return AuthService.update_profile(db, user, request)

@router.get("/me", response_model=UserProfileResponse, summary="Get Current User Profile")
def get_me(user: User = Depends(get_current_user)):
    """Retrieve profile data and onboarding status for the currently authenticated user."""
    return user


@router.post("/forgot-password", response_model=MessageResponse, summary="Request Password Reset Code")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send a 6-digit password reset code to a registered email address."""
    return AuthService.forgot_password(db, request)


@router.post("/verify-reset-otp", response_model=ResetTokenResponse, summary="Verify Password Reset Code")
def verify_reset_otp(request: ResetOTPRequest, db: Session = Depends(get_db)):
    """Validate the password reset code and return a short-lived reset token."""
    return AuthService.verify_reset_otp(db, request)


@router.post("/reset-password", response_model=MessageResponse, summary="Reset Password with Token")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Set a new password using the token returned by /verify-reset-otp."""
    return AuthService.reset_password(db, request)
