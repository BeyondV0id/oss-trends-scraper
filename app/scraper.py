import re
import logging
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Repo, TrendingRepo
from app.config import settings

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

GITHUB_API_HEADERS = {
    "User-Agent": "SourceSurf-TrendingScraper",
    "Accept": "application/vnd.github+json",
}

if settings.GITHUB_TOKEN:
    GITHUB_API_HEADERS["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"


# ─────────────────── Scraping ───────────────────


def scrape_trending_page(language: str = "", since: str = "daily") -> list[dict]:
    """Scrape the GitHub trending page and return a list of repo dicts."""
    url = "https://github.com/trending"
    if language:
        url += f"/{language}"

    logger.info("Scraping trending: language=%s since=%s", language or "all", since)

    try:
        resp = httpx.get(url, params={"since": since}, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as exc:
        logger.error("Failed to fetch GitHub trending page: %s", exc)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    repos: list[dict] = []

    for row in soup.find_all("article", class_="Box-row"):
        try:
            h2_tag = row.find("h2", class_="h3")
            if not h2_tag:
                continue
            a_tag = h2_tag.find("a")
            if not a_tag:
                continue

            href = a_tag.get("href", "")
            if not href or href.count("/") < 2:
                continue

            parts = href.strip("/").split("/")
            if len(parts) < 2:
                continue

            owner, repo_name = parts[0], parts[1]

            stars_earned = 0
            stats_section = row.find("div", class_="f6")
            if stats_section:
                for span in stats_section.find_all("span"):
                    text = span.get_text(strip=True).lower()
                    if "star" in text:
                        match = re.search(r"([\d,]+)\s*star", text)
                        if match:
                            num_str = match.group(1).replace(",", "")
                            stars_earned = int(num_str) if num_str.isdigit() else 0
                        break

            repos.append({
                "owner": owner,
                "repo": repo_name,
                "stars_earned": stars_earned,
            })
        except Exception as exc:
            logger.warning("Skipping row: %s", exc)

    logger.info("Scraped %d repos", len(repos))
    return repos


# ─────────────────── GitHub API enrichment ───────────────────


async def fetch_repo_details(client: httpx.AsyncClient, owner: str, repo_name: str) -> dict | None:
    """Fetch full repo metadata from the GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo_name}"
    try:
        resp = await client.get(url, headers=GITHUB_API_HEADERS)
        if resp.status_code == 200:
            return resp.json()
        logger.warning("GitHub API returned %d for %s/%s", resp.status_code, owner, repo_name)
    except Exception as exc:
        logger.error("GitHub API error for %s/%s: %s", owner, repo_name, exc)
    return None


# ─────────────────── DB operations ───────────────────


async def upsert_repo(session: AsyncSession, data: dict) -> int:
    """Insert or update a repo and return its id."""
    stmt = pg_insert(Repo).values(
        github_id=data["id"],
        owner=data["owner"]["login"],
        repo_name=data["name"],
        full_name=data["full_name"],
        url=data["html_url"],
        description=data.get("description"),
        language=data.get("language"),
        stargazers_count=data.get("stargazers_count", 0),
        forks_count=data.get("forks_count", 0),
        watchers_count=data.get("watchers_count", 0),
        open_issues_count=data.get("open_issues_count", 0),
        created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")) if data.get("created_at") else None,
        updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")) if data.get("updated_at") else None,
        last_synced_at=datetime.utcnow(),
    ).on_conflict_do_update(
        index_elements=["github_id"],
        set_={
            "stargazers_count": data.get("stargazers_count", 0),
            "forks_count": data.get("forks_count", 0),
            "watchers_count": data.get("watchers_count", 0),
            "open_issues_count": data.get("open_issues_count", 0),
            "updated_at": datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")) if data.get("updated_at") else None,
            "last_synced_at": datetime.utcnow(),
        },
    ).returning(Repo.id)

    result = await session.execute(stmt)
    row = result.fetchone()
    return row[0]


async def upsert_trending(session: AsyncSession, repo_id: int, period: str, stars_earned: int):
    """Insert or update a trending entry."""
    stmt = pg_insert(TrendingRepo).values(
        repo_id=repo_id,
        period=period,
        stars_earned=stars_earned,
        created_at=datetime.utcnow(),
    ).on_conflict_do_update(
        constraint="repo_period_idx",
        set_={
            "stars_earned": stars_earned,
            "created_at": datetime.utcnow(),
        },
    )
    await session.execute(stmt)


async def clear_trending(session: AsyncSession, period: str):
    """Remove all trending entries for a given period."""
    await session.execute(delete(TrendingRepo).where(TrendingRepo.period == period))


# ─────────────────── Main orchestrator ───────────────────


async def scrape_and_store(session: AsyncSession, period: str = "daily", language: str = "") -> dict:
    """
    Full pipeline: scrape → enrich via GitHub API → store in DB.
    Returns summary stats.
    """
    scraped_repos = scrape_trending_page(language=language, since=period)

    if not scraped_repos:
        return {"scraped": 0, "errors": 0, "message": "No repos scraped"}

    # Clear old entries for this period before inserting fresh data
    await clear_trending(session, period)

    synced = 0
    errors = 0

    async with httpx.AsyncClient(timeout=20) as client:
        for item in scraped_repos:
            try:
                gh_data = await fetch_repo_details(client, item["owner"], item["repo"])
                if not gh_data:
                    errors += 1
                    continue

                repo_id = await upsert_repo(session, gh_data)
                await upsert_trending(session, repo_id, period, item["stars_earned"])
                synced += 1
            except Exception as exc:
                logger.error("Error processing %s/%s: %s", item["owner"], item["repo"], exc)
                errors += 1

    await session.commit()
    logger.info("Scrape complete for period=%s: synced=%d errors=%d", period, synced, errors)
    return {"scraped": synced, "errors": errors, "message": f"Scraped {synced} repos for {period}"}
