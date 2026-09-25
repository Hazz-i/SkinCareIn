import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from core.database import Base
from models.user import User
from schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    VerifyOTPRequest,
    ResendVerificationRequest
)
from services.auth_service import AuthService
from core.config import settings

# Use in-memory SQLite database for unit testing
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def production_env(monkeypatch):
    """Email verification is mandatory — the behaviour a real deployment must have."""
    monkeypatch.setattr(settings, "APP_ENV", "production")

@pytest.fixture
def local_env(monkeypatch):
    """Development mode: no real inbox, so the verification step is relaxed."""
    monkeypatch.setattr(settings, "APP_ENV", "local")

def test_register_creates_unverified_member_with_otp():
    db = TestingSessionLocal()
    req = UserRegisterRequest(
        email="newmember@example.com",
        username="newmember",
        password="Password123!"
    )
    result = AuthService.register_user(db, req)
    assert result["email"] == "newmember@example.com"
    assert result["is_verified"] is False
    
    # Verify in DB
    user = db.query(User).filter(User.email == "newmember@example.com").first()
    assert user is not None
    assert user.role == "member"
    assert user.is_verified is False
    assert user.verification_otp is not None
    assert len(user.verification_otp) == 6
    assert user.verification_token is not None
    db.close()

def test_login_blocked_if_unverified(production_env):
    db = TestingSessionLocal()
    req = UserRegisterRequest(
        email="unverified@example.com",
        username="unverified",
        password="Password123!"
    )
    AuthService.register_user(db, req)

    login_req = UserLoginRequest(
        email="unverified@example.com",
        password="Password123!"
    )
    with pytest.raises(HTTPException) as exc_info:
        AuthService.authenticate_user(db, login_req)
    assert exc_info.value.status_code == 403
    assert "not verified" in exc_info.value.detail.lower()
    db.close()

def test_verify_otp_success_and_login_allowed():
    db = TestingSessionLocal()
    req = UserRegisterRequest(
        email="otpuser@example.com",
        username="otpuser",
        password="Password123!"
    )
    AuthService.register_user(db, req)
    user = db.query(User).filter(User.email == "otpuser@example.com").first()
    otp_code = user.verification_otp

    # Verify with correct OTP
    verify_req = VerifyOTPRequest(email="otpuser@example.com", otp=otp_code)
    verify_res = AuthService.verify_otp(db, verify_req)
    assert "verified" in verify_res["message"].lower()

    # User should now be verified
    db.refresh(user)
    assert user.is_verified is True

    # Login should succeed
    login_req = UserLoginRequest(email="otpuser@example.com", password="Password123!")
    auth_data = AuthService.authenticate_user(db, login_req)
    assert "access_token" in auth_data
    assert auth_data["is_onboarded"] is False
    assert auth_data["role"] == "member"
    db.close()

def test_verify_otp_expired(production_env):
    db = TestingSessionLocal()
    req = UserRegisterRequest(
        email="expired@example.com",
        username="expired",
        password="Password123!"
    )
    AuthService.register_user(db, req)
    user = db.query(User).filter(User.email == "expired@example.com").first()
    # Expire the OTP
    user.otp_expires_at = datetime.utcnow() - timedelta(minutes=1)
    db.commit()

    verify_req = VerifyOTPRequest(email="expired@example.com", otp=user.verification_otp)
    with pytest.raises(HTTPException) as exc_info:
        AuthService.verify_otp(db, verify_req)
    assert exc_info.value.status_code == 400
    assert "expired" in exc_info.value.detail.lower()
    db.close()

def test_resend_verification():
    db = TestingSessionLocal()
    req = UserRegisterRequest(
        email="resend@example.com",
        username="resend",
        password="Password123!"
    )
    AuthService.register_user(db, req)
    user = db.query(User).filter(User.email == "resend@example.com").first()
    first_token = user.verification_token

    resend_req = ResendVerificationRequest(email="resend@example.com")
    resend_res = AuthService.resend_verification(db, resend_req)
    assert "resent" in resend_res["message"].lower()

    db.refresh(user)
    assert user.verification_token != first_token
    db.close()

def test_local_env_accepts_any_otp(local_env):
    db = TestingSessionLocal()
    AuthService.register_user(db, UserRegisterRequest(
        email="localuser@example.com",
        username="localuser",
        password="Password123!"
    ))
    user = db.query(User).filter(User.email == "localuser@example.com").first()
    real_otp = user.verification_otp
    wrong_otp = "000000" if real_otp != "000000" else "111111"

    result = AuthService.verify_otp(
        db, VerifyOTPRequest(email="localuser@example.com", otp=wrong_otp)
    )
    assert result["is_verified"] is True

    db.refresh(user)
    assert user.is_verified is True
    db.close()

def test_local_env_login_skips_verification_gate(local_env):
    db = TestingSessionLocal()
    AuthService.register_user(db, UserRegisterRequest(
        email="localflow@example.com",
        username="localflow",
        password="Password123!"
    ))

    # No OTP verification call at all — signing in must still work on a local env.
    auth_data = AuthService.authenticate_user(
        db, UserLoginRequest(email="localflow@example.com", password="Password123!")
    )
    assert "access_token" in auth_data

    user = db.query(User).filter(User.email == "localflow@example.com").first()
    assert user.is_verified is True
    db.close()
