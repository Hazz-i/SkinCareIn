import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from server import app
from core.database import Base, get_db
from models.user import User
from core.security import create_access_token

from sqlalchemy.pool import StaticPool

# Test database in-memory
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def test_user():
    db = TestingSessionLocal()
    user = User(
        email="onboarding_test@example.com",
        username="onboarding_test",
        hashed_password="dummy_hashed_password",
        role="member",
        is_active=True,
        is_verified=True,
        is_onboarded=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id
    db.close()
    return user_id

def test_onboarding_flow(test_user):
    token = create_access_token(data={"sub": str(test_user), "email": "onboarding_test@example.com", "role": "member"})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "first_name": "Wahid",
        "last_name": "Hasyim",
        "age": 24,
        "gender": "male",
        "skin_type": "oily",
        "avoided_ingredients": ["Coconut Oil", "Mineral Oil", "Fragrance"]
    }

    response = client.post("/api/v1/auth/onboarding", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Wahid"
    assert data["last_name"] == "Hasyim"
    assert data["age"] == 24
    assert data["skin_type"] == "oily"
    assert data["avoided_ingredients"] == ["Coconut Oil", "Mineral Oil", "Fragrance"]
    assert data["is_onboarded"] is True

    # Check GET /me returns updated profile
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["is_onboarded"] is True
    assert me_data["skin_type"] == "oily"

def test_onboarding_validation_failure(test_user):
    token = create_access_token(data={"sub": str(test_user), "email": "onboarding_test@example.com", "role": "member"})
    headers = {"Authorization": f"Bearer {token}"}

    # Invalid skin_type
    bad_payload = {
        "first_name": "Wahid",
        "age": 24,
        "gender": "male",
        "skin_type": "invalid_skin_type"
    }
    response = client.post("/api/v1/auth/onboarding", json=bad_payload, headers=headers)
    assert response.status_code == 422

def test_update_profile(test_user):
    token = create_access_token(data={"sub": str(test_user), "email": "onboarding_test@example.com", "role": "member"})
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {
        "first_name": "UpdatedName",
        "skin_type": "sensitive"
    }
    response = client.put("/api/v1/auth/profile", json=update_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "UpdatedName"
    assert data["skin_type"] == "sensitive"
