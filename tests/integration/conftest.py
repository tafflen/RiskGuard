"""PostgreSQL/PostGIS integration fixtures guarded against accidental production use."""

import os
from collections.abc import AsyncIterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def _test_database_url() -> str:
    url = os.getenv("TEST_DATABASE_URL")
    if url is None:
        pytest.skip("TEST_DATABASE_URL is not configured; integration database tests are skipped.")
    if "riskguard_test" not in url:
        pytest.fail("TEST_DATABASE_URL must target a dedicated database named riskguard_test.")
    return url


@pytest.fixture(scope="session", autouse=True)
def migrate_test_database() -> str:
    url = _test_database_url()
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    try:
        command.upgrade(Config("alembic.ini"), "head")
        yield url
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous


@pytest.fixture
async def db_session(migrate_test_database: str) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(migrate_test_database, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        await session.execute(
            text(
                "TRUNCATE risk_assessments, weather_observations, incidents, shelters, hazards, "
                "locations, user_devices, users CASCADE"
            )
        )
        await session.commit()
        yield session
    await engine.dispose()
