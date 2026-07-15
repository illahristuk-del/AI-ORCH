import asyncio

from search_mcp.adapters.db import Base, make_engine, make_session_factory
from search_mcp.adapters.orm import CandidateOrmModel
from search_mcp.data import CANDIDATES


async def main() -> None:
    engine = make_engine()
    session_factory = make_session_factory(engine)
    async with session_factory() as session:
        for c in CANDIDATES:
            session.add(
                CandidateOrmModel(
                    id=c.id,
                    name=c.name,
                    skills=list(c.skills),
                    experience_years=c.experience_years,
                )
            )
        await session.commit()
    await engine.dispose()
    print("SEEDED")


asyncio.run(main())
