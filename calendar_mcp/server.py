import os
from datetime import datetime
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from uuid import UUID
from typing import Literal, cast

from mcp import ServerSession
from mcp.server.fastmcp import Context, FastMCP
from sqlalchemy.ext.asyncio import AsyncEngine

from search_mcp.adapters.db import make_engine, make_session_factory
from calendar_mcp.adapters.postgres import PostgresCalendarRepository
from calendar_mcp.store import CalendarRepository
from calendar_mcp.models import Interview
from search_mcp.adapters import orm 

@dataclass
class AppContext:
    repo: CalendarRepository

_app_ctx: AppContext | None = None

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    global _app_ctx
    engine: AsyncEngine = make_engine()
    session_factory = make_session_factory(engine)
    async with session_factory() as session:
        _app_ctx = AppContext(repo=PostgresCalendarRepository(session))
        try:
            yield _app_ctx
        finally:
            _app_ctx = None
    await engine.dispose()

mcp = FastMCP("calendar", lifespan=app_lifespan, port=8001)

@mcp.tool()
async def book_interview(
    candidate_id: str,
    scheduled_at: str,
    ctx: Context[ServerSession, AppContext],
) -> str:
    repo = ctx.request_context.lifespan_context.repo

    try:
        cid = UUID(candidate_id)
    except ValueError:
        return f"Invalid candidate id: {candidate_id}"
    
    try: 
        when = datetime.fromisoformat(scheduled_at)
    except ValueError:
        return f"Invalid date: {scheduled_at}"
    
    interview = Interview(candidate_id=cid, scheduled_at=when)

    booked = await repo.book(interview)

    return f"Interview booked: candidate {booked.candidate_id}, date: {booked.scheduled_at}"

if __name__ == "__main__":
    raw = os.getenv("MCP_TRANSPORT", "stdio")
    if raw not in ("stdio", "streamable-http"):
        raise SystemExit(f"Unknown transport: {raw}")
    transport = cast(Literal["stdio", "streamable-http"], raw)
    mcp.run(transport=transport)
