from uuid import UUID
from typing import Any

from mcp.server.fastmcp import FastMCP

from search_mcp.data import CANDIDATES
from search_mcp.store import InMemoryCandidateRepository

mcp = FastMCP("candidate-search")

_repo = InMemoryCandidateRepository(CANDIDATES)


@mcp.tool()
async def search_candidates(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Find candidates by skills.

    Args:
    query: space-separated keywords, for example, "python backend".
    A candidate is included in the search results if at least one skill matches.
    limit: maximum number of candidates in the response.

    Returns:
        A list of candidates sorted by relevance.
        Empty list if there are no matches.
    """

    results = await _repo.search(query, limit)

    if results == []:
        print("Nobody found")

    return [c.model_dump(mode="json") for c in results]


@mcp.resource("candidate://{candidate_id}")
async def get_candidate(candidate_id: str) -> str:
    """Retrieve the full candidate details using their ID.

    The ID is obtained from the `search_candidates` results.
    """

    try:
        parsed_id = UUID(candidate_id)
    except ValueError:
        return f"Invalid candidate id: {candidate_id}"

    result = await _repo.get(parsed_id)

    if result is None:
        return (
            f"Candidate with ID {candidate_id} not found."
            "Use search_candidates to get current IDs."
        )
    return result.model_dump_json()


if __name__ == "__main__":
    mcp.run()
