import re
import logging
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Repo, TrendingRepo

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _parse_count(text: str) -> int:
    text = text.strip().replace(",", "")
    try:
        return int(text)
    except ValueError:
        return 0


def scrape_trending_page(language: str = "", since: str = "daily") -> list[dict]:
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
            full_name = f"{owner}/{repo_name}"

            desc_tag = row.find("p")
            description = desc_tag.get_text(strip=True) if desc_tag else None

            lang_span = row.find("span", itemprop="programmingLanguage")
            language_name = lang_span.get_text(strip=True) if lang_span else None

            total_stars = 0
            forks = 0
            stars_earned = 0

            stats_div = row.find("div", class_="f6")
            if stats_div:
                for link in stats_div.find_all("a", href=True):
                    href_attr = link["href"]
                    num_text = link.get_text(strip=True)
                    if href_attr.endswith("/stargazers"):
                        total_stars = _parse_count(num_text)
                    elif "/forks" in href_attr or "/network" in href_attr:
                        forks = _parse_count(num_text)

                for span in stats_div.find_all("span"):
                    text = span.get_text(strip=True).lower()
                    if "star" in text and ("today" in text or "this week" in text or "this month" in text):
                        match = re.search(r"([\d,]+)", text)
                        if match:
                            stars_earned = _parse_count(match.group(1))
                        break

            repos.append({
                "owner": owner,
                "repo_name": repo_name,
                "full_name": full_name,
                "url": f"https://github.com/{full_name}",
                "description": description,
                "language": language_name,
                "stargazers_count": total_stars,
                "forks_count": forks,
                "stars_earned": stars_earned,
            })
        except Exception as exc:
            logger.warning("Skipping row: %s", exc)

    logger.info("Scraped %d repos from page", len(repos))
    return repos


async def upsert_repo(session: AsyncSession, data: dict) -> int:
    stmt = pg_insert(Repo).values(
        owner=data["owner"],
        repo_name=data["repo_name"],
        full_name=data["full_name"],
        url=data["url"],
        description=data.get("description"),
        language=data.get("language"),
        stargazers_count=data.get("stargazers_count", 0),
        forks_count=data.get("forks_count", 0),
        watchers_count=0,
        open_issues_count=0,
        last_synced_at=datetime.utcnow(),
    ).on_conflict_do_update(
        index_elements=["full_name"],
        set_={
            "description": data.get("description"),
            "language": data.get("language"),
            "stargazers_count": data.get("stargazers_count", 0),
            "forks_count": data.get("forks_count", 0),
            "last_synced_at": datetime.utcnow(),
        },
    ).returning(Repo.id)

    result = await session.execute(stmt)
    row = result.fetchone()
    return row[0]


async def upsert_trending(session: AsyncSession, repo_id: int, period: str, stars_earned: int):
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
    await session.execute(delete(TrendingRepo).where(TrendingRepo.period == period))


async def scrape_and_store(session: AsyncSession, period: str = "daily", language: str = "") -> dict:
    scraped_repos = scrape_trending_page(language=language, since=period)

    if not scraped_repos:
        return {"scraped": 0, "errors": 0, "message": "No repos scraped"}

    await clear_trending(session, period)

    synced = 0
    errors = 0

    for item in scraped_repos:
        try:
            async with session.begin_nested():
                repo_id = await upsert_repo(session, item)
                await upsert_trending(session, repo_id, period, item["stars_earned"])
            synced += 1
        except Exception as exc:
            logger.error("Error processing %s: %s", item["full_name"], exc)
            errors += 1

    await session.commit()
    logger.info("Scrape complete for period=%s: synced=%d errors=%d", period, synced, errors)
    return {"scraped": synced, "errors": errors, "message": f"Scraped {synced} repos for {period}"}
