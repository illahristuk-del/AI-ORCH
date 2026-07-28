import logging

import httpx

from search_mcp.adapters.auth import create_token
from search_mcp.adapters.tracing import trace_id_var

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
    trace_id = trace_id_var.get()
    headers = {"Authorization": f"Bearer {token}", "X-Trace-Id": trace_id}

    try:
        async with httpx.AsyncClient(timeout=10) as http:
            await http.post(f"{audit_url}/audit", json=payload, headers=headers)
    except Exception as e:
        logger.warning("log_event failed: %s", e)
