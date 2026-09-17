import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from server import app
from core.database import Base, get_db
from models.user import User
from models.product import Product
from models.education import EducationArticle
from models.article import NewsArticle
from core.security import create_access_token

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

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)

def test_dashboard_endpoint_structure_and_filtering():
    db = TestingSessionLocal()
    # Create user with oily skin who avoids "Coconut Oil" and "Fragrance"
    user = User(
        email="dashboard_user@example.com",
        username="dashuser",
        first_name="John",
        last_name="Doe",
        age=26,
        gender="male",
        skin_type="oily",
        avoided_ingredients=["Coconut Oil", "Fragrance"],
        role="member",
        is_active=True,
        is_verified=True,
        is_onboarded=True
    )
    db.add(user)

    # Add 2 products: 1 safe, 1 containing Coconut Oil (must be excluded)
    safe_product = Product(
        title="Safe Hydrating Gel",
        price="$15",
        description="Lightweight oil-free hydration",
        image_url="https://example.com/safe.jpg",
        ingredients="Water, Glycerin, Niacinamide, Hyaluronic Acid",
        type="oily"
    )
    unsafe_product = Product(
        title="Coconut Nourishing Cream",
        price="$20",
        description="Rich moisture cream",
        image_url="https://example.com/unsafe.jpg",
        ingredients="Water, Coconut Oil, Shea Butter, Fragrance",
        type="oily"
    )
    # Add an education article and a news article
    edu = EducationArticle(
        title="Understanding Skincare Actives",
        link="https://example.com/edu1",
        image_url="https://example.com/edu1.jpg",
        date="2026-09-15",
        category="Actives"
    )
    news = NewsArticle(
        title="Beauty Industry News Today",
        link="https://example.com/news1",
        image_url="https://example.com/news1.jpg",
        date="2026-09-17",
        category="Industry"
    )
    db.add_all([safe_product, unsafe_product, edu, news])
    db.commit()
    db.refresh(user)
    user_id = user.id
    db.close()

    token = create_access_token(data={"sub": str(user_id), "email": "dashboard_user@example.com", "role": "member"})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/dashboard", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # User summary
    assert data["user_summary"]["name"] == "John Doe"
    assert data["user_summary"]["skin_type"] == "oily"
    assert data["user_summary"]["avoided_ingredients"] == ["Coconut Oil", "Fragrance"]

    # Tips and warnings
    assert len(data["skin_health_tips"]) > 0
    assert len(data["dermatological_warnings"]) > 0

    # Negative product filtering: safe product must be present, unsafe product must be omitted!
    rec_titles = [p["title"] for p in data["recommended_products"]]
    assert "Safe Hydrating Gel" in rec_titles
    assert "Coconut Nourishing Cream" not in rec_titles

    # Content feeds
    assert len(data["recent_educations"]) >= 1
    assert data["recent_educations"][0]["title"] == "Understanding Skincare Actives"
    assert len(data["recent_news"]) >= 1
    assert data["recent_news"][0]["title"] == "Beauty Industry News Today"
