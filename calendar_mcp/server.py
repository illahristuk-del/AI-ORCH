import os
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

import uvicorn
from mcp import ServerSession
from mcp.server.fastmcp import Context, FastMCP
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from calendar_mcp.adapters.postgres import PostgresCalendarRepository
from calendar_mcp.models import Interview
from calendar_mcp.store import CalendarRepository
from search_mcp.adapters.config import settings
from search_mcp.adapters.db import make_engine, make_session_factory


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


async def check_token(request: Request, call_next: Any) -> Response:
    expected = f"Bearer {settings.agent_token}"

    if not secrets.compare_digest(request.headers.get("authorization", ""), expected):
        return JSONResponse(
            status_code=401, content={"detail": "Invalid token or missing token"}
        )
    response: Response = await call_next(request)
    return response


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

    try:
        interview = Interview(candidate_id=cid, scheduled_at=when)
    except ValueError as e:
        return f"Cannot book {e}"

    booked = await repo.book(interview)

    return f"Interview booked: candidate {booked.candidate_id}, date: {booked.scheduled_at}"


if __name__ == "__main__":
    raw = os.getenv("MCP_TRANSPORT", "stdio")
    if raw not in ("stdio", "streamable-http"):
        raise SystemExit(f"Unknown transport: {raw}")
    if raw == "stdio":
        mcp.run(transport="stdio")
    else:
        app = mcp.streamable_http_app()

        app.add_middleware(BaseHTTPMiddleware, dispatch=check_token)

        uvicorn.run(app, host="127.0.0.1", port=8001)
