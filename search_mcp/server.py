import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Annotated, Any
from uuid import UUID

import jwt
import uvicorn
from mcp import ServerSession
from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from opentelemetry.instrumentation.starlette import StarletteInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from prometheus_client import make_asgi_app

from search_mcp.adapters.auth import verify_token
from search_mcp.adapters.db import make_engine, make_session_factory
from search_mcp.adapters.logging_config import setup_logging
from search_mcp.adapters.postgres import PostgresCandidateRepository
from search_mcp.store import CandidateRepository
from search_mcp.adapters.tracing import trace_id_var
from search_mcp.adapters.otel import setup_tracing

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    repo: CandidateRepository


_app_ctx: AppContext | None = None


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    global _app_ctx
    engine: AsyncEngine = make_engine()
    session_factory = make_session_factory(engine)
    async with session_factory() as session:
        _app_ctx = AppContext(repo=PostgresCandidateRepository(session))
        try:
            yield _app_ctx
        finally:
            _app_ctx = None
    await engine.dispose()


mcp = FastMCP("candidate-search", lifespan=app_lifespan)


async def check_token(request: Request, call_next: Any) -> Response:
    if request.url.path in ("/metrics", "/metrics/"):
        response: Response = await call_next(request)
        return response

    trace_id = request.headers.get("x-trace-id", "")
    trace_id_var.set(trace_id)
    auth_header = request.headers.get("authorization", "")
    token = auth_header.removeprefix("Bearer ")

    try:
        verify_token(token)
    except jwt.InvalidTokenError:
        logger.warning("rejected: invalid token")
        return JSONResponse(status_code=401, content={"detail": "Invalid or missing token"})
    response: Response = await call_next(request)
    return response


@mcp.tool()
async def search_candidates(
    query: str,
    ctx: Context[ServerSession, AppContext],
    limit: Annotated[int, Field(ge=1, le=50)] = 5,
) -> list[dict[str, Any]]:
    """Find candidates by skills.

    Args:
    query: space-separated keywords, for example, "python backend".
    A candidate is included in the search results if at least one skill matches.
    limit: maximum number of candidates in the response.

    Returns:
        A list of candidates sorted by relevance.
        Empty list if there are no matches.
    """

    repo = ctx.request_context.lifespan_context.repo

    results = await repo.search(query, limit)

    return [c.model_dump(mode="json") for c in results]


@mcp.resource("candidate://{candidate_id}")
async def get_candidate(candidate_id: str) -> str:
    """Retrieve the full candidate details using their ID.

    The ID is obtained from the `search_candidates` results.
    """

    if _app_ctx is None:
        return "Server is not initialized"

    try:
        parsed_id = UUID(candidate_id)
    except ValueError:
        return f"Invalid candidate id: {candidate_id}"

    result = await _app_ctx.repo.get(parsed_id)

    if result is None:
        return (
            f"Candidate with ID {candidate_id} not found. Use search_candidates to get current IDs."
        )
    return result.model_dump_json()


if __name__ == "__main__":
    setup_logging()
    setup_tracing("hr mcp")

    raw = os.getenv("MCP_TRANSPORT", "stdio")
    if raw not in ("stdio", "streamable-http"):
        raise SystemExit(f"Unknown transport: {raw}")

    if raw == "stdio":
        mcp.run(transport="stdio")
    else:
        app = mcp.streamable_http_app()
        app.add_middleware(BaseHTTPMiddleware, dispatch=check_token)

        StarletteInstrumentor.instrument_app(app)
        SQLAlchemyInstrumentor().instrument()

        app.mount("/metrics", make_asgi_app())

        uvicorn.run(app, host="127.0.0.1", port=8000)
