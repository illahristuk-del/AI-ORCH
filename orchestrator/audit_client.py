import httpx

from search_mcp.adapters.config import settings


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

    headers = {"Authorization": f"Bearer {settings.registry_token}"}

    try:
        async with httpx.AsyncClient(timeout=10) as http:
            await http.post(f"{settings.audit_url}/audit", json=payload, headers=headers)
    except Exception as e:
        print(f"Audit error: {e}")
