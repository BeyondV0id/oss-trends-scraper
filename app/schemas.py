from datetime import datetime
from pydantic import BaseModel


# ---------- Repo ----------
class RepoBase(BaseModel):
    github_id: int | None = None
    owner: str
    repo_name: str
    full_name: str
    url: str
    description: str | None = None
    language: str | None = None
    stargazers_count: int = 0
    forks_count: int = 0
    watchers_count: int = 0
    open_issues_count: int = 0


class RepoOut(RepoBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_synced_at: datetime | None = None

    class Config:
        from_attributes = True


# ---------- Trending ----------
class TrendingRepoOut(BaseModel):
    id: int
    period: str
    stars_earned: int
    created_at: datetime | None = None
    repo: RepoOut

    class Config:
        from_attributes = True


class TrendingRepoSimple(BaseModel):
    """Flattened response: repo info + stars_earned."""
    id: int
    github_id: int | None = None
    owner: str
    repo_name: str
    full_name: str
    url: str
    description: str | None = None
    language: str | None = None
    stargazers_count: int = 0
    forks_count: int = 0
    stars_earned: int = 0
    period: str

    class Config:
        from_attributes = True


# ---------- Scrape request ----------
class ScrapeRequest(BaseModel):
    period: str = "daily"  # daily | weekly | monthly
    language: str = ""


class ScrapeResponse(BaseModel):
    message: str
    scraped: int
    errors: int
