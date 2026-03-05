import logging

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models import Repo, TrendingRepo
from app.schemas import TrendingRepoSimple, ScrapeRequest, ScrapeResponse
from app.scraper import scrape_and_store

logger = logging.getLogger(__name__)

router = APIRouter()


# ───────── Public: Get trending repos ─────────


@router.get("/trending", response_model=list[TrendingRepoSimple])
async def get_trending(
    period: str = Query("daily", description="daily | weekly | monthly | all"),
    db: AsyncSession = Depends(get_db),
):
    """Return trending repos for a given period."""
    stmt = select(TrendingRepo).options(selectinload(TrendingRepo.repo))

    if period != "all":
        stmt = stmt.where(TrendingRepo.period == period)

    stmt = stmt.order_by(TrendingRepo.stars_earned.desc())
    result = await db.execute(stmt)
    rows = result.scalars().all()

    out: list[TrendingRepoSimple] = []
    for row in rows:
        if not row.repo:
            continue
        out.append(TrendingRepoSimple(
            id=row.repo.id,
            github_id=row.repo.github_id,
            owner=row.repo.owner,
            repo_name=row.repo.repo_name,
            full_name=row.repo.full_name,
            url=row.repo.url,
            description=row.repo.description,
            language=row.repo.language,
            stargazers_count=row.repo.stargazers_count,
            forks_count=row.repo.forks_count,
            stars_earned=row.stars_earned,
            period=row.period,
        ))

    return out


# ───────── Admin: Trigger a scrape ─────────


@router.post("/scrape", response_model=ScrapeResponse)
async def trigger_scrape(
    body: ScrapeRequest,
    db: AsyncSession = Depends(get_db),
    x_admin_secret: str = Header(...),
):
    """Manually trigger a scrape. Requires admin secret header."""
    if x_admin_secret != settings.ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Unauthorized")

    if body.period not in {"daily", "weekly", "monthly"}:
        raise HTTPException(status_code=400, detail="Invalid period. Use daily, weekly, or monthly.")

    result = await scrape_and_store(db, period=body.period, language=body.language)
    return ScrapeResponse(**result)


# ───────── Health check ─────────


@router.get("/health")
async def health():
    return {"status": "ok", "service": "trending-scraper"}
