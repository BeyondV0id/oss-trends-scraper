import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db, close_db
from app.routes import router
from app.scheduler import start_scheduler, stop_scheduler, scheduled_scrape

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    logger.info("Starting Trending Scraper microservice...")
    await init_db()
    logger.info("Database tables created / verified.")

    # Run an initial scrape on startup
    try:
        await scheduled_scrape()
    except Exception as exc:
        logger.error("Initial scrape failed: %s", exc)

    start_scheduler()

    yield

    # ── Shutdown ──
    stop_scheduler()
    await close_db()
    logger.info("Trending Scraper microservice stopped.")


app = FastAPI(
    title="SourceSurf Trending Scraper",
    description="Microservice that scrapes GitHub trending repos, stores them in PostgreSQL, and exposes a REST API.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "service": "trending-scraper",
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    from app.config import settings

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
