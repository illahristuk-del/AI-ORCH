import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
import jwt
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
from search_mcp.adapters.auth import create_token, verify_token
from search_mcp.adapters.config import settings
from search_mcp.adapters.logging_config import setup_logging
from search_mcp.adapters.tracing import trace_id_var

logger = logging.getLogger(__name__)


async def register_in_registry() -> None:
    payload = {
        "id": AGENT_ID,
        "name": "hr_recruiter",
        "description": SEARCH_SKILL.description,
        "skills": list(SEARCH_SKILL.tags),
        "url": settings.hr_agent_url,
    }
    token = create_token("hr_recruiter")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with httpx.AsyncClient(timeout=10) as http:
            await http.delete(f"{settings.registry_url}/agents/{AGENT_ID}", headers=headers)
            await http.post(f"{settings.registry_url}/agents", json=payload, headers=headers)
    except Exception:
        logger.warning("registry failed: %s")


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

    trace_id = request.headers.get("x-trace-id", "")
    trace_id_var.set(trace_id)
    auth_token = request.headers.get("authorization", "")
    token = auth_token.removeprefix("Bearer ")

    try:
        verify_token(token)
    except jwt.InvalidTokenError:
        return JSONResponse(status_code=401, content={"detail": "Invalid token or missing token"})

    response = await call_next(request)
    return response


def main() -> None:
    setup_logging()

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
