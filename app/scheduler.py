import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.database import AsyncSessionLocal
from app.scraper import scrape_and_store

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def scheduled_scrape():
    """Run scrapes for all periods."""
    logger.info("Scheduled scrape starting...")
    for period in ["daily", "weekly", "monthly"]:
        async with AsyncSessionLocal() as session:
            try:
                result = await scrape_and_store(session, period=period)
                logger.info("Scheduled scrape [%s]: %s", period, result)
            except Exception as exc:
                logger.error("Scheduled scrape [%s] failed: %s", period, exc)
    logger.info("Scheduled scrape complete.")


def start_scheduler():
    """Register the scrape job and start the scheduler."""
    scheduler.add_job(
        scheduled_scrape,
        trigger=IntervalTrigger(minutes=settings.SCRAPE_INTERVAL_MINUTES),
        id="trending_scrape",
        name="Scrape GitHub Trending",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler started — scraping every %d minutes", settings.SCRAPE_INTERVAL_MINUTES
    )


def stop_scheduler():
    """Shut down the scheduler gracefully."""
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped.")
