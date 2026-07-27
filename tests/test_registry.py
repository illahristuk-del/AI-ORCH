from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from registry.adapters.orm import AgentOrmModel
from registry.adapters.postgres import PostgresAgentRepository
from registry.models import Agent, AgentUpdate


async def _seed(session: AsyncSession, *agents: Agent) -> None:
    for a in agents:
        session.add(
            AgentOrmModel(
                id=a.id,
                name=a.name,
                description=a.description,
                skills=list(a.skills),
                url=a.url,
            )
        )

    await session.flush()


async def test_get_return_agent_from_db(session: AsyncSession) -> None:
    weather_agent = Agent(
        name="weather",
        description="weather agent",
        skills=("weather", "search", "check", "location"),
        url="http://weather123/",
    )
    await _seed(session, weather_agent)

    repo = PostgresAgentRepository(session)
    result = await repo.get(weather_agent.id)

    assert result is not None
    assert result == weather_agent
    assert isinstance(result.skills, tuple)


async def test_get_return_all_agents_from_db(session: AsyncSession) -> None:
    weather_agent1 = Agent(
        name="weather11238",
        description="weather agent2",
        skills=("weather", "search", "check", "location"),
        url="http://weather1241113/",
    )
    weather_agent2 = Agent(
        name="weather81928",
        description="weather agent3",
        skills=("weather", "search", "check", "location"),
        url="http://weather191239/",
    )
    weather_agent3 = Agent(
        name="weather1231",
        description="weather agent4",
        skills=("weather", "search", "check", "location"),
        url="http://weather12345/",
    )

    await _seed(session, weather_agent1, weather_agent2, weather_agent3)

    repo = PostgresAgentRepository(session)
    result = await repo.get_all()

    assert len(result) == 3
    assert {a.name for a in result} == {"weather11238", "weather81928", "weather1231"}


async def test_create_agent(session: AsyncSession) -> None:
    new_agent = Agent(
        name="weather",
        description="weather agent",
        skills=("weather", "search", "check", "location"),
        url="http://weather123/",
    )

    repo = PostgresAgentRepository(session)
    await repo.create(new_agent)

    result = await repo.get(new_agent.id)

    assert result is not None
    assert result.name == "weather"


async def test_get_returns_none_for_unknown_id(session: AsyncSession) -> None:
    repo = PostgresAgentRepository(session)
    result = await repo.get(uuid4())

    assert result is None


async def test_update_agent_name_description_skills(
    session: AsyncSession, sample_agent: Agent
) -> None:
    await _seed(session, sample_agent)
    repo = PostgresAgentRepository(session)

    result = await repo.update(
        sample_agent.id,
        AgentUpdate(
            name="new_agent_weather_name",
            description="new_agent_weather_description",
            skills=("nothing",),
        ),
    )

    updated_agent = await repo.get(sample_agent.id)

    assert result is not None
    assert result.name == "new_agent_weather_name"

    assert updated_agent is not None
    assert updated_agent.name == "new_agent_weather_name"
    assert updated_agent.description == "new_agent_weather_description"
    assert updated_agent.skills == ("nothing",)
    assert updated_agent.url == sample_agent.url


async def test_update_update_unknown_agent_from_db(session: AsyncSession) -> None:
    repo = PostgresAgentRepository(session)
    result = await repo.update(uuid4(), AgentUpdate(name="name", description="description"))

    assert result is None


async def test_delete_agent_from_db(session: AsyncSession, sample_agent: Agent) -> None:
    await _seed(session, sample_agent)

    repo = PostgresAgentRepository(session)
    result = await repo.delete(sample_agent.id)

    assert result is True
    assert await repo.get(sample_agent.id) is None


async def test_delete_unknown_agent_from_db(session: AsyncSession) -> None:
    repo = PostgresAgentRepository(session)
    result = await repo.delete(uuid4())

    assert result is False


async def test_search_agent_by_skill(session: AsyncSession, sample_agent: Agent) -> None:
    await _seed(session, sample_agent)

    repo = PostgresAgentRepository(session)
    result = await repo.search_by_skill("weather")

    assert len(result) == 1
    assert result[0].id == sample_agent.id


async def test_search_agent_by_unknown_skill(session: AsyncSession) -> None:
    repo = PostgresAgentRepository(session)
    result = await repo.search_by_skill(skill="gaming")

    assert result == []
