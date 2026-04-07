"""
One-shot CI scrape script.

Scrapes GitHub trending and writes results directly into the scraper's own
PostgreSQL database (the same DB the FastAPI server reads from).

This allows CI to be the scheduler — no long-running server needed in CI.
The FastAPI server (deployed separately) simply reads from this DB.

Usage:
    python run_scrape.py

Environment variables:
    DATABASE_URL   - Scraper's Postgres connection string (required)
    SCRAPE_MODE    - daily | weekly | monthly  (default: daily)
    GITHUB_TOKEN   - (optional) GitHub token to avoid rate limiting
"""

import asyncio
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    period = os.environ.get("SCRAPE_MODE", "daily").strip().lower()

    if period not in {"daily", "weekly", "monthly"}:
        logger.error("SCRAPE_MODE must be daily | weekly | monthly. Got: %s", period)
        sys.exit(1)

    # Validate DB is reachable before doing any work
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        logger.error("DATABASE_URL is not set. Aborting.")
        sys.exit(1)

    logger.info("Starting one-shot scrape: period=%s", period)

    # Import here so the env is fully set before SQLAlchemy reads config
    from app.database import init_db, close_db, AsyncSessionLocal
    from app.scraper import scrape_and_store

    # Verify DB connectivity
    try:
        await init_db()
        logger.info("Database connected.")
    except Exception as e:
        logger.error("Could not connect to database: %s", e)
        sys.exit(1)

    # Run the scrape and store results
    try:
        async with AsyncSessionLocal() as session:
            result = await scrape_and_store(session, period=period)
            logger.info("Scrape result: %s", result)

            if result.get("scraped", 0) == 0:
                logger.warning(
                    "No repos were scraped — GitHub trending page may have changed layout."
                )
    except Exception as e:
        logger.error("Scrape failed: %s", e)
        await close_db()
        sys.exit(1)

    await close_db()
    logger.info("Done. Scrape for period=%s complete.", period)


if __name__ == "__main__":
    # Fix for Windows where psycopg v3 needs SelectorEventLoop
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
