# models/__init__.py
from models.user import User
from models.product import Product
from models.article import NewsArticle, NewsArticleDetail
from models.education import EducationArticle, EducationArticleDetail
from models.uv_index import UVIndexCache

__all__ = [
    "User",
    "Product",
    "NewsArticle",
    "NewsArticleDetail",
    "EducationArticle",
    "EducationArticleDetail",
    "UVIndexCache"
]
