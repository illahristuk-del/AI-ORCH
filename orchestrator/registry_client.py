from typing import Any, cast

import httpx

from search_mcp.adapters.auth import create_token


async def fetch_agents(registry_url: str) -> list[dict[str, Any]]:
    token = create_token("orchestrator")
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=10, headers=headers) as http:
        response = await http.get(f"{registry_url}/agents")
        response.raise_for_status()
        return cast(list[dict[str, Any]], response.json())
