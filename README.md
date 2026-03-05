# Trending Scraper Microservice

A standalone microservice that scrapes GitHub trending repositories, stores them in PostgreSQL, and exposes a REST API.

## Architecture

```
┌─────────────────────────────────────────────┐
│          Trending Scraper Service            │
│                                             │
│  ┌───────────┐  ┌──────────┐  ┌──────────┐ │
│  │  FastAPI   │  │ Scraper  │  │Scheduler │ │
│  │  (routes)  │  │ (BS4 +   │  │(APSched) │ │
│  │           │  │  httpx)  │  │          │ │
│  └─────┬─────┘  └────┬─────┘  └────┬─────┘ │
│        │             │             │        │
│        └──────┬──────┘             │        │
│               │                    │        │
│        ┌──────▼──────┐      triggers│        │
│        │ SQLAlchemy   │◄────────────┘        │
│        │ (asyncpg)   │                      │
│        └──────┬──────┘                      │
└───────────────┼─────────────────────────────┘
                │
         ┌──────▼──────┐
         │ PostgreSQL   │
         │ (Supabase)   │
         └─────────────┘
```

## Tables

| Table            | Description                                                  |
| ---------------- | ------------------------------------------------------------ |
| `repos`          | Full GitHub repo metadata (owner, stars, forks, etc.)        |
| `trending_repos` | Trending entries linked to repos, with period & stars earned |

## API Endpoints

| Method | Path                         | Auth                    | Description                                   |
| ------ | ---------------------------- | ----------------------- | --------------------------------------------- |
| `GET`  | `/api/trending?period=daily` | —                       | Get trending repos (daily/weekly/monthly/all) |
| `POST` | `/api/scrape`                | `x-admin-secret` header | Manually trigger a scrape                     |
| `GET`  | `/api/health`                | —                       | Health check                                  |
| `GET`  | `/docs`                      | —                       | Swagger UI                                    |

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your DATABASE_URL and secrets
```

### 3. Run locally

```bash
python -m app.main
# or
uvicorn app.main:app --reload --port 8001
```

### 4. Run with Docker

```bash
docker build -t trending-scraper .
docker run -p 8001:8001 --env-file .env trending-scraper
```

## How It Works

1. **On startup**: creates DB tables if they don't exist, runs an initial scrape for all periods (daily/weekly/monthly).
2. **Scheduler**: automatically re-scrapes every N minutes (configurable via `SCRAPE_INTERVAL_MINUTES`).
3. **Scrape pipeline**:
   - Scrapes `github.com/trending` with BeautifulSoup
   - Enriches each repo via the GitHub REST API (`/repos/{owner}/{name}`)
   - Upserts repo metadata into `repos` table
   - Upserts trending entry into `trending_repos` table
4. **API**: serves the stored trending data to the frontend/backend.

## Environment Variables

| Variable                  | Default     | Description                                |
| ------------------------- | ----------- | ------------------------------------------ |
| `DATABASE_URL`            | —           | PostgreSQL connection string               |
| `GITHUB_TOKEN`            | —           | Optional GitHub PAT for higher rate limits |
| `ADMIN_SECRET`            | `change-me` | Secret for admin endpoints                 |
| `SCRAPE_INTERVAL_MINUTES` | `360`       | Auto-scrape interval                       |
| `PORT`                    | `8001`      | Server port                                |
| `HOST`                    | `0.0.0.0`   | Server bind address                        |
