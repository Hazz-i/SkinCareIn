# tests/test_education_service.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base
from models.education import EducationArticle, EducationArticleDetail
from services.education_service import EducationService
from unittest.mock import patch

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_lazy_cache_education_detail(db):
    test_link = "https://www.eduskincare.eu.org/edu-1"
    fake_scraped = {
        "Title": "Edu Title",
        "Author": "Doctor",
        "Date": "2026-09-17",
        "Cover_Image": "https://img.com/edu.jpg",
        "Content": "Edu article body content"
    }
    with patch("services.education_service.get_educations_details", return_value=fake_scraped):
        detail = EducationService.get_or_scrape_education_detail(db, test_link)
        assert detail.title == "Edu Title"
        assert db.query(EducationArticleDetail).filter_by(article_link=test_link).count() == 1

    # Second request hits cache without calling scraper
    with patch("services.education_service.get_educations_details", side_effect=Exception("Should not be called")):
        cached = EducationService.get_or_scrape_education_detail(db, test_link)
        assert cached.title == "Edu Title"
