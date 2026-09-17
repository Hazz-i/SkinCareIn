# tests/test_database_models.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base
from models.user import User
from models.article import NewsArticle, NewsArticleDetail
from models.education import EducationArticle, EducationArticleDetail
from models.product import Product

TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

def test_create_user_model(db_session):
    user = User(username="testuser", email="test@example.com", hashed_password="pw", role="user")
    db_session.add(user)
    db_session.commit()
    assert user.id is not None
    assert user.role == "user"
    assert user.is_active is True

def test_create_product_model(db_session):
    prod = Product(title="Serum Vitamin C", price="120000", description="Serum mencerahkan", ingredients="Aqua, Vitamin C")
    db_session.add(prod)
    db_session.commit()
    assert prod.id is not None
    assert prod.title == "Serum Vitamin C"

def test_create_article_and_detail_cache_models(db_session):
    article = NewsArticle(title="News 1", link="https://kompas.com/news1", page_number=1)
    detail = NewsArticleDetail(article_link="https://kompas.com/news1", title="News 1", content_markdown="Full content")
    db_session.add_all([article, detail])
    db_session.commit()
    assert article.id is not None
    assert detail.id is not None
    assert detail.article_link == "https://kompas.com/news1"

def test_create_education_and_detail_cache_models(db_session):
    edu = EducationArticle(title="Edu 1", link="https://eduskincare.eu.org/edu1", page_number=1)
    edu_detail = EducationArticleDetail(article_link="https://eduskincare.eu.org/edu1", title="Edu 1", content_markdown="Edu content")
    db_session.add_all([edu, edu_detail])
    db_session.commit()
    assert edu.id is not None
    assert edu_detail.id is not None
