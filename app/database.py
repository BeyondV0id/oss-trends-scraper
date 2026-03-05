from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.config import settings

# SQLAlchemy async engine using psycopg v3 via greenlet (works on all platforms)
engine = create_async_engine(
    settings.DATABASE_URL, echo=False, pool_size=5, max_overflow=10,
    connect_args={"prepare_threshold": 0},
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    """Dependency that yields a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Verify DB connection on startup (tables managed by Alembic)."""
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))


async def close_db():
    """Dispose of the engine on shutdown."""
    await engine.dispose()
