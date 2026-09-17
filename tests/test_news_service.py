# tests/test_news_service.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base
from models.article import NewsArticle, NewsArticleDetail
from services.news_service import NewsService
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

def test_lazy_cache_news_detail(db):
    test_link = "https://www.kompas.com/skincare-article-1"
    
    # 1. First access (cache MISS) -> triggers scrape and saves to DB
    fake_scraped = [{
        "Title": "Scraped Title",
        "Cover_Image": "https://img.com/pic.jpg",
        "Date": "2026-09-17",
        "Source": "Kompas",
        "Author": "Editor",
        "Content": "Scraped article body text"
    }]
    with patch("services.news_service.get_news", return_value=fake_scraped):
        detail = NewsService.get_or_scrape_news_detail(db, test_link)
        assert detail.title == "Scraped Title"
        assert db.query(NewsArticleDetail).filter_by(article_link=test_link).count() == 1

    # 2. Second access (cache HIT) -> loads from DB without calling scraper
    with patch("services.news_service.get_news", side_effect=Exception("Should not be called")):
        cached_detail = NewsService.get_or_scrape_news_detail(db, test_link)
        assert cached_detail.title == "Scraped Title"
