import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Annotated, Any, Literal, cast
from uuid import UUID

from mcp import ServerSession
from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

from search_mcp.data import CANDIDATES
from search_mcp.store import CandidateRepository, InMemoryCandidateRepository


@dataclass
class AppContext:
    repo: CandidateRepository


_app_ctx: AppContext | None = None


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    global _app_ctx
    _app_ctx = AppContext(repo=InMemoryCandidateRepository(CANDIDATES))
    try:
        yield _app_ctx
    finally:
        _app_ctx = None


mcp = FastMCP("candidate-search", lifespan=app_lifespan)


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
            f"Candidate with ID {candidate_id} not found. "
            "Use search_candidates to get current IDs."
        )
    return result.model_dump_json()


if __name__ == "__main__":
    raw = os.getenv("MCP_TRANSPORT", "stdio")
    if raw not in ("stdio", "streamable-http"):
        raise SystemExit(f"Unknown transport: {raw}")
    transport = cast(Literal["stdio", "streamable-http"], raw)
    mcp.run(transport=transport)
