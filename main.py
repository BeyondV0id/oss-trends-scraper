from fastapi import FastAPI, Query
from trendingScrapper import get_trending_repos

app = FastAPI(title="SourceSurf Scraper")


@app.get("/scrape")
def scrape(period: str = Query("daily")):
    """Scrape GitHub trending page and return parsed repos."""
    repos = get_trending_repos(since=period)
    return {"repos": repos, "period": period, "count": len(repos)}


@app.get("/health")
def health():
    return {"status": "ok"}
