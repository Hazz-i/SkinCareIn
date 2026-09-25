# services/education_service.py
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from models.education import EducationArticle, EducationArticleDetail
from helper.educations import get_educations_list, get_educations_details
from core.logger import log_action
from fastapi import HTTPException

# Cached content is refreshed at most once per day.
SYNC_TTL_HOURS = 24

# Safety cap so a runaway pagination loop can never hammer the source.
MAX_SYNC_PAGES = 10

class EducationService:
    @staticmethod
    def sync_educations_from_source(
        db: Session, max_pages: int = 2, until_exhausted: bool = False
    ) -> int:
        """Scrape Lab Muffin pages and upsert them. With `until_exhausted`, keep paging
        until a page returns no articles or the page cap is reached."""
        log_action("scrap", f"Starting background sync of education topics (up to {max_pages} pages)...")
        synced_count = 0
        for page in range(1, max_pages + 1):
            try:
                scraped_data, _ = get_educations_list(page_number=page)
            except Exception as e:
                log_action("scrap", f"Error scraping education page {page}: {e}", level="warning")
                break

            if not scraped_data:
                # No articles on this page -> reached the end of the archive.
                break

            for item in scraped_data:
                link = item.get("Link")
                if not link:
                    continue
                existing = db.query(EducationArticle).filter(EducationArticle.link == link).first()
                if existing:
                    existing.title = item.get("Title", existing.title)
                    existing.image_url = item.get("Image", existing.image_url)
                    existing.snippet = item.get("Snippet", existing.snippet)
                    existing.date = str(item.get("Date", existing.date))
                    existing.category = item.get("Category", existing.category)
                    existing.fetched_at = datetime.utcnow()
                else:
                    new_edu = EducationArticle(
                        title=item.get("Title", ""),
                        link=link,
                        image_url=item.get("Image", ""),
                        snippet=item.get("Snippet", ""),
                        date=str(item.get("Date", "")),
                        category=item.get("Category", ""),
                        page_number=page,
                        fetched_at=datetime.utcnow()
                    )
                    db.add(new_edu)
                    synced_count += 1
            db.commit()
        log_action("db", f"Synchronized education topics cache. Added {synced_count} new records.")
        return synced_count

    @staticmethod
    def get_cached_educations_list(db: Session, page: int = 1, page_size: int = 15) -> dict:
        total = db.query(EducationArticle).count()
        latest = db.query(func.max(EducationArticle.fetched_at)).scalar()

        # Refresh once the TTL window has elapsed, not only when the table is empty.
        is_stale = latest is None or (datetime.utcnow() - latest) > timedelta(hours=SYNC_TTL_HOURS)
        if total == 0 or is_stale:
            # Walk the whole archive (not just page 1) so later pages are cached too.
            EducationService.sync_educations_from_source(
                db, max_pages=MAX_SYNC_PAGES, until_exhausted=True
            )
            total = db.query(EducationArticle).count()

        offset = (page - 1) * page_size
        items = db.query(EducationArticle).order_by(EducationArticle.fetched_at.desc()).offset(offset).limit(page_size).all()
        log_action("db", f"Returned {len(items)} cached education topics for page {page}")
        return {"educations": items, "total": total, "page": page}

    @staticmethod
    def get_or_scrape_education_detail(db: Session, article_link: str) -> EducationArticleDetail:
        # 1. Check cache
        cached = db.query(EducationArticleDetail).filter(EducationArticleDetail.article_link == article_link).first()
        if cached:
            log_action("cache", f"Cache HIT for education detail: {article_link}")
            return cached

        # 2. Cache MISS -> scrape once
        log_action("cache", f"Cache MISS for education detail: {article_link} -> scraping from EduSkincare...")
        try:
            scraped = get_educations_details(article_link)
        except Exception as e:
            log_action("scrap", f"Failed to scrape education detail {article_link}: {e}", level="error")
            scraped = None

        if not scraped:
            log_action("scrap", f"Education detail not found on source: {article_link}", level="error")
            raise HTTPException(status_code=404, detail="Education article detail not found.")

        new_detail = EducationArticleDetail(
            article_link=article_link,
            title=scraped.get("Title", ""),
            author=scraped.get("Author", "Dr Michelle Wong (Lab Muffin)"),
            date=str(scraped.get("Date", "")),
            cover_image=scraped.get("Cover_Image", ""),
            content_markdown=scraped.get("Content", "")
        )
        db.add(new_detail)
        db.commit()
        db.refresh(new_detail)
        log_action("db", f"Saved new education detail permanently to DB for link: {article_link}")
        return new_detail
