# scheduler/jobs.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from core.database import SessionLocal
from services.news_service import NewsService
from services.education_service import EducationService
from core.logger import log_action

scheduler = AsyncIOScheduler()

def run_daily_scraping_sync():
    log_action("schedule", "Running daily 24-hour scraping synchronization for articles and educations...")
    db = SessionLocal()
    try:
        news_synced = NewsService.sync_news_from_source(db, max_pages=3)
        edu_synced = EducationService.sync_educations_from_source(db, max_pages=2)
        log_action("schedule", f"Daily sync finished. Synced {news_synced} news, {edu_synced} educations.")
    except Exception as e:
        log_action("schedule", f"Error during scheduled daily sync: {str(e)}", level="error")
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(
        run_daily_scraping_sync,
        trigger=IntervalTrigger(hours=24),
        id="daily_scraping_sync",
        name="Sync articles and educations daily",
        replace_existing=True
    )
    scheduler.start()
    log_action("schedule", "APScheduler started (running every 24 hours).")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        log_action("schedule", "APScheduler stopped.")
