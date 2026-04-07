import os
from dotenv import load_dotenv

load_dotenv()


def _normalize_db_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Settings:
    def __init__(self) -> None:
        raw_url = os.environ.get("DATABASE_URL", "").strip()
        if not raw_url:
            raise RuntimeError("DATABASE_URL environment variable is not set")
        self.DATABASE_URL: str = _normalize_db_url(raw_url)
        self.DATABASE_URL_SYNC: str = self.DATABASE_URL

        self.GITHUB_TOKEN: str | None = os.environ.get("GITHUB_TOKEN")
        self.ADMIN_SECRET: str = os.environ.get("ADMIN_SECRET", "change-me")
        self.SCRAPE_INTERVAL_MINUTES: int = int(os.environ.get("SCRAPE_INTERVAL_MINUTES", "360"))
        self.PORT: int = int(os.environ.get("PORT", "8001"))
        self.HOST: str = os.environ.get("HOST", "0.0.0.0")


settings = Settings()
