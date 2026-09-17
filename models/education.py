# models/education.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from core.database import Base

class EducationArticle(Base):
    __tablename__ = "education_articles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    link = Column(String(1000), unique=True, index=True, nullable=False)
    image_url = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)
    date = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    page_number = Column(Integer, default=1, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class EducationArticleDetail(Base):
    __tablename__ = "education_article_details"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    article_link = Column(String(1000), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    author = Column(String(150), nullable=True)
    date = Column(String(100), nullable=True)
    cover_image = Column(Text, nullable=True)
    content_markdown = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
