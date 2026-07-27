import logging

import httpx

from search_mcp.adapters.auth import create_token

logger = logging.getLogger(__name__)


async def log_event(
    audit_url: str,
    actor: str,
    action: str,
    resource: str | None,
    status: str,
    details: str | None,
) -> None:
    payload = {
        "actor": actor,
        "action": action,
        "resource": resource,
        "status": status,
        "details": details,
    }

    token = create_token("orchestrator")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient(timeout=10) as http:
            await http.post(f"{audit_url}/audit", json=payload, headers=headers)
    except Exception as e:
        logger.warning("log_vent failed: %s", e)
