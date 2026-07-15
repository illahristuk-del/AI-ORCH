from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from search_mcp.adapters.orm import CandidateOrmModel
from search_mcp.models import Candidate
from search_mcp.store import rank_candidates


class PostgresCandidateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: CandidateOrmModel) -> Candidate:
        return Candidate(
            id=orm.id,
            name=orm.name,
            skills=tuple(orm.skills),
            experience_years=orm.experience_years,
        )

    async def get(self, candidate_id: UUID) -> Candidate | None:
        result = await self._session.execute(
            select(CandidateOrmModel).where(CandidateOrmModel.id == candidate_id)
        )

        orm = result.scalar_one_or_none()

        if orm is None:
            return None
        return self._to_domain(orm)

    async def search(self, query: str, limit: int) -> list[Candidate]:
        result = await self._session.execute(select(CandidateOrmModel))
        orm_rows = result.scalars().all()
        candidates = [self._to_domain(row) for row in orm_rows]
        return rank_candidates(candidates, query, limit)
