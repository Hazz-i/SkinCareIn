# services/news_service.py
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from models.article import NewsArticle, NewsArticleDetail
from helper.news import get_news_list, get_news
from core.logger import log_action
from fastapi import HTTPException

# Cached content is refreshed at most once every 2 days (48 hours).
SYNC_TTL_HOURS = 48

# BeautyJournal serves the feed in pages of 15; a short page means the feed is exhausted.
NEWS_PAGE_SIZE = 15
MAX_SYNC_PAGES = 10

class NewsService:
    @staticmethod
    def sync_news_from_source(
        db: Session, max_pages: int = 3, until_exhausted: bool = False
    ) -> int:
        """Scrape the feed and upsert it. With `until_exhausted`, keep paging (like the
        site's infinite scroll) until a short/empty page or the page cap is reached."""
        log_action("scrap", f"Starting background sync of news list (up to {max_pages} pages)...")
        synced_count = 0
        for page in range(1, max_pages + 1):
            try:
                scraped_data = get_news_list(page=page, page_size=NEWS_PAGE_SIZE)
            except Exception as e:
                log_action("scrap", f"Error scraping page {page}: {e}", level="warning")
                break
            articles = scraped_data.get("Article_List", []) if scraped_data else []
            if not articles:
                # No more items on the remote feed.
                break
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
            if until_exhausted and len(articles) < NEWS_PAGE_SIZE:
                # Reached the end of the feed.
                break
        log_action("db", f"Synchronized news articles cache. Added {synced_count} new records.")
        return synced_count

    @staticmethod
    def get_cached_news_list(db: Session, page: int = 1, page_size: int = 15) -> dict:
        total = db.query(NewsArticle).count()
        latest = db.query(func.max(NewsArticle.fetched_at)).scalar()

        # Refresh once the TTL window has elapsed, not only when the table is empty.
        is_stale = latest is None or (datetime.utcnow() - latest) > timedelta(hours=SYNC_TTL_HOURS)
        if total == 0 or is_stale:
            # The tab opening triggers a full walk of the feed (infinite scroll order),
            # so every page requested later is already cached for the next visitor.
            NewsService.sync_news_from_source(db, max_pages=MAX_SYNC_PAGES, until_exhausted=True)
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
            raise HTTPException(status_code=404, detail="News article detail not found.")

        item = scraped[0]
        new_detail = NewsArticleDetail(
            article_link=article_link,
            title=item.get("Title", ""),
            cover_image=item.get("Cover_Image") or item.get("ImageUrl") or "",
            date=item.get("Date", ""),
            source=item.get("Source", "BeautyJournal"),
            author=item.get("Author", ""),
            content_markdown=item.get("Content", "")
        )
        db.add(new_detail)
        db.commit()
        db.refresh(new_detail)
        log_action("db", f"Saved new article detail permanently to DB for link: {article_link}")
        return new_detail
