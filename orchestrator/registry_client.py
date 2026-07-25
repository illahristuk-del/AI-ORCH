from typing import Any, cast

import httpx


async def fetch_agents(registry_url: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=10) as http:
        response = await http.get(f"{registry_url}/agents")
        response.raise_for_status()
        return cast(list[dict[str, Any]], response.json())
