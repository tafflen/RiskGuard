"""Async SQLAlchemy session lifecycle and database health checks."""

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings


def build_engine(settings: Settings) -> AsyncEngine:
    """Build one pooled asyncpg engine from validated process configuration."""
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout_seconds,
        pool_recycle=settings.db_pool_recycle_seconds,
    )


@lru_cache
def get_engine() -> AsyncEngine:
    """Return the application-wide database engine; never create one per request."""
    return build_engine(get_settings())


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return sessions configured not to expire attributes after commit."""
    return async_sessionmaker(get_engine(), expire_on_commit=False, autoflush=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield a transaction-scoped session and reliably roll back on failure."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Release pooled database connections during application shutdown."""
    await get_engine().dispose()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


async def check_database_health() -> str:
    """Verify database reachability and PostGIS availability for future readiness checks."""
    async with get_engine().connect() as connection:
        version = await connection.scalar(text("SELECT PostGIS_Version()"))
    if not isinstance(version, str) or not version:
        msg = "PostGIS is unavailable or returned an invalid version."
        raise RuntimeError(msg)
    return version
