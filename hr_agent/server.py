import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from hr_agent.card import AGENT_CARD, AGENT_ID, SEARCH_SKILL
from hr_agent.executor import HRRecruiterExecutor
from search_mcp.adapters.config import settings


async def register_in_registry() -> None:
    payload = {
        "id": AGENT_ID,
        "name": "hr_recruiter",
        "description": SEARCH_SKILL.description,
        "skills": list(SEARCH_SKILL.tags),
        "url": settings.hr_agent_url,
    }
    headers = {"Authorization": f"Bearer {settings.registry_token}"}
    try:
        async with httpx.AsyncClient(timeout=10) as http:
            await http.delete(
                f"{settings.registry_url}/agents/{AGENT_ID}", headers=headers
            )
            await http.post(
                f"{settings.registry_url}/agents", json=payload, headers=headers
            )
    except Exception as e:
        print(f"Registry unavailable, skipping registration: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await register_in_registry()
    yield


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def check_token(request: Request, call_next: Any) -> Response:
    if request.url.path == "/.well-known/agent-card.json":
        response: Response = await call_next(request)
        return response
    expected = f"Bearer {settings.agent_token}"
    if not secrets.compare_digest(request.headers.get("authorization", ""), expected):
        return JSONResponse(
            status_code=401, content={"detail": "Invalid token or missing token"}
        )
    response = await call_next(request)
    return response


def main() -> None:
    executor = HRRecruiterExecutor(settings.mcp_url, settings.anthropic_api_key)
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        agent_card=AGENT_CARD,
    )

    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(AGENT_CARD),
        jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url="/"),
    )

    uvicorn.run(app, host="127.0.0.1", port=9999)


if __name__ == "__main__":
    main()
