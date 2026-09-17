# tests/test_auth.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from core.database import Base, get_db
from models.user import User
from routers.auth import router as auth_router

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
app.include_router(auth_router, prefix="/api/v1/auth")

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_register_and_login_flow():
    # 1. Register user
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": "user@example.com",
        "username": "user1",
        "password": "password123",
        "role": "member"
    })
    assert reg_resp.status_code == 201
    data = reg_resp.json()
    assert data["email"] == "user@example.com"
    assert data["is_verified"] is False

    # 2. Verify OTP
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "user@example.com").first()
    otp_code = user.verification_otp
    db.close()

    verify_resp = client.post("/api/v1/auth/verify-otp", json={
        "email": "user@example.com",
        "otp": otp_code
    })
    assert verify_resp.status_code == 200

    # 3. Login
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "user@example.com",
        "password": "password123"
    })
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 4. Get profile (/me)
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "user1"
    assert me_resp.json()["role"] == "member"
    assert me_resp.json()["is_verified"] is True
