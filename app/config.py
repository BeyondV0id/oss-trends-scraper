import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:password@localhost:5432/trending_db",
    )
    # Convert standard postgres:// URL to psycopg async format if needed
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

    # Sync URL for Alembic migrations (psycopg v3 sync mode)
    DATABASE_URL_SYNC: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:password@localhost:5432/trending_db",
    )
    # Ensure it uses psycopg v3 dialect (not psycopg2)
    if DATABASE_URL_SYNC.startswith("postgresql://"):
        DATABASE_URL_SYNC = DATABASE_URL_SYNC.replace("postgresql://", "postgresql+psycopg://", 1)

    GITHUB_TOKEN: str | None = os.getenv("GITHUB_TOKEN", None)
    ADMIN_SECRET: str = os.getenv("ADMIN_SECRET", "change-me")
    SCRAPE_INTERVAL_MINUTES: int = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "360"))  # 6 hours
    PORT: int = int(os.getenv("PORT", "8001"))
    HOST: str = os.getenv("HOST", "0.0.0.0")


settings = Settings()
