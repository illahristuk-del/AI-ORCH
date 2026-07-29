from typing import Any, cast

import httpx

from search_mcp.adapters.auth import create_token
from search_mcp.adapters.tracing import trace_id_var


async def fetch_agents(registry_url: str) -> list[dict[str, Any]]:
    token = create_token("orchestrator")
    trace_id = trace_id_var.get()
    headers = {"Authorization": f"Bearer {token}", "X-Trace-Id": trace_id}
    async with httpx.AsyncClient(timeout=10, headers=headers) as http:
        response = await http.get(f"{registry_url}/agents")
        response.raise_for_status()
        return cast(list[dict[str, Any]], response.json())
