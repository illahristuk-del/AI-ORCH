import pytest
from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from search_mcp.adapters.db import Base, make_engine, make_session_factory
from registry.models import Agent

TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_orch_test"


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = make_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = make_session_factory(engine)
    async with factory() as s:
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def sample_agent() -> Agent:
    return Agent(
        name="weather",
        description="weather agent",
        skills=("weather", "search"),
        url="http://weather123/",
    )
