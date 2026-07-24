from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from registry.adapters.orm import AgentOrmModel
from registry.models import Agent, AgentUpdate


class PostgresAgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(orm_agent: AgentOrmModel) -> Agent:
        return Agent(
            id=orm_agent.id,
            name=orm_agent.name,
            description=orm_agent.description,
            skills=tuple(orm_agent.skills),
            url=orm_agent.url,
        )

    async def get(self, agent_id: UUID) -> Agent | None:
        agent = await self.session.get(AgentOrmModel, agent_id)

        if agent is None:
            return None

        return self._to_domain(agent)

    async def get_all(self) -> list[Agent]:
        result = await self.session.execute(select(AgentOrmModel))
        all_rows = result.scalars().all()
        agents = [self._to_domain(row) for row in all_rows]
        return agents

    async def create(self, agent: Agent) -> Agent:
        new_agent = AgentOrmModel(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            skills=list(agent.skills),
            url=agent.url,
        )

        self.session.add(new_agent)
        await self.session.commit()

        return self._to_domain(new_agent)

    async def update(self, agent_id: UUID, data: AgentUpdate) -> Agent | None:
        agent = await self.session.get(AgentOrmModel, agent_id)
        if agent is None:
            return None
        if data.name is not None:
            agent.name = data.name
        if data.description is not None:
            agent.description = data.description
        if data.skills is not None:
            agent.skills = list(data.skills)
        await self.session.commit()

        return self._to_domain(agent)

    async def delete(self, agent_id: UUID) -> bool:
        agent = await self.session.get(AgentOrmModel, agent_id)

        if agent is None:
            return False

        await self.session.delete(agent)
        await self.session.commit()

        return True

    async def search_by_skill(self, skill: str) -> list[Agent]:
        result = await self.session.execute(
            select(AgentOrmModel).where(AgentOrmModel.skills.contains([skill]))
        )
        rows = result.scalars().all()

        return [self._to_domain(row) for row in rows]
