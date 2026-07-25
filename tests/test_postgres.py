from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from search_mcp.adapters.orm import CandidateOrmModel
from search_mcp.adapters.postgres import PostgresCandidateRepository
from search_mcp.models import Candidate


async def _seed(session: AsyncSession, *candidates: Candidate) -> None:
    for c in candidates:
        session.add(
            CandidateOrmModel(
                id=c.id,
                name=c.name,
                skills=list(c.skills),
                experience_years=c.experience_years,
            )
        )
    await session.commit()


async def test_get_returns_candidate_from_db(session: AsyncSession) -> None:
    karl = Candidate(name="Karl", skills=("python", "sql"), experience_years=3)
    await _seed(session, karl)

    repo = PostgresCandidateRepository(session)
    result = await repo.get(karl.id)

    assert result == karl


async def test_get_returns_none_for_unknown_id(session: AsyncSession) -> None:
    repo = PostgresCandidateRepository(session)
    result = await repo.get(uuid4())

    assert result is None


async def test_to_domain_converts_orm_correctly(session: AsyncSession) -> None:
    karl = Candidate(name="Karl", skills=("python", "sql"), experience_years=3)
    await _seed(session, karl)

    repo = PostgresCandidateRepository(session)
    result = await repo.get(karl.id)

    assert result is not None
    assert isinstance(result, Candidate)
    assert isinstance(result.skills, tuple)
    assert result.skills == ("python", "sql")
    assert result.id == karl.id
