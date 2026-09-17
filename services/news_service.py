# services/news_service.py
from datetime import datetime
from sqlalchemy.orm import Session
from models.article import NewsArticle, NewsArticleDetail
from helper.news import get_news_list, get_news
from core.logger import log_action
from fastapi import HTTPException

class NewsService:
    @staticmethod
    def sync_news_from_source(db: Session, max_pages: int = 3) -> int:
        log_action("scrap", f"Starting background sync of news list (pages 1 to {max_pages})...")
        synced_count = 0
        for page in range(1, max_pages + 1):
            try:
                scraped_data = get_news_list(page=page)
            except Exception as e:
                log_action("scrap", f"Error scraping page {page}: {e}", level="warning")
                continue
            articles = scraped_data.get("Article_List", []) if scraped_data else []
            for item in articles:
                link = item.get("Link")
                if not link:
                    continue
                existing = db.query(NewsArticle).filter(NewsArticle.link == link).first()
                if existing:
                    existing.title = item.get("Title", existing.title)
                    existing.image_url = item.get("Image", existing.image_url)
                    existing.date = item.get("Date", existing.date)
                    existing.category = item.get("Category", existing.category)
                    existing.fetched_at = datetime.utcnow()
                else:
                    new_art = NewsArticle(
                        title=item.get("Title", ""),
                        link=link,
                        image_url=item.get("Image", ""),
                        date=item.get("Date", ""),
                        category=item.get("Category", ""),
                        page_number=page,
                        fetched_at=datetime.utcnow()
                    )
                    db.add(new_art)
                    synced_count += 1
            db.commit()
        log_action("db", f"Synchronized news articles cache. Added {synced_count} new records.")
        return synced_count

    @staticmethod
    def get_cached_news_list(db: Session, page: int = 1, page_size: int = 15) -> dict:
        total = db.query(NewsArticle).count()
        # If DB is empty, trigger an initial sync
        if total == 0:
            NewsService.sync_news_from_source(db, max_pages=1)
            total = db.query(NewsArticle).count()

        offset = (page - 1) * page_size
        articles = db.query(NewsArticle).order_by(NewsArticle.fetched_at.desc()).offset(offset).limit(page_size).all()
        log_action("db", f"Returned {len(articles)} cached news articles for page {page}")
        return {"articles": articles, "total": total, "page": page}

    @staticmethod
    def get_or_scrape_news_detail(db: Session, article_link: str) -> NewsArticleDetail:
        # 1. Check cache in database
        cached = db.query(NewsArticleDetail).filter(NewsArticleDetail.article_link == article_link).first()
        if cached:
            log_action("cache", f"Cache HIT for news detail: {article_link}")
            return cached

        # 2. Cache MISS -> scrape once
        log_action("cache", f"Cache MISS for news detail: {article_link} -> scraping from source...")
        try:
            scraped = get_news(article_link)
        except Exception as e:
            log_action("scrap", f"Failed to scrape article detail {article_link}: {e}", level="error")
            scraped = None

        if not scraped:
            log_action("scrap", f"Article detail not found on source: {article_link}", level="error")
            raise HTTPException(status_code=404, detail="Detail berita tidak ditemukan.")

        item = scraped[0]
        new_detail = NewsArticleDetail(
            article_link=article_link,
            title=item.get("Title", ""),
            cover_image=item.get("Cover_Image") or item.get("ImageUrl") or "",
            date=item.get("Date", ""),
            source=item.get("Source", "Kompas.com"),
            author=item.get("Author", ""),
            content_markdown=item.get("Content", "")
        )
        db.add(new_detail)
        db.commit()
        db.refresh(new_detail)
        log_action("db", f"Saved new article detail permanently to DB for link: {article_link}")
        return new_detail
