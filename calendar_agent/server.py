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
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator

from calendar_agent.card import AGENT_CARD, AGENT_ID, BOOK_SKILLS
from calendar_agent.executor import CalendarBooker
from search_mcp.adapters.auth import create_token, verify_token
from search_mcp.adapters.config import settings
from search_mcp.adapters.logging_config import setup_logging
from search_mcp.adapters.tracing import trace_id_var
from search_mcp.adapters.otel import setup_tracing

logger = logging.getLogger(__name__)


async def register_in_registry() -> None:
    payload = {
        "id": AGENT_ID,
        "name": "calendar_booker",
        "description": BOOK_SKILLS.description,
        "skills": list(BOOK_SKILLS.tags),
        "url": settings.calendar_agent_url,
    }
    token = create_token("calendar_booker")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with httpx.AsyncClient(timeout=10) as http:
            await http.delete(f"{settings.registry_url}/agents/{AGENT_ID}", headers=headers)
            await http.post(f"{settings.registry_url}/agents", json=payload, headers=headers)
    except Exception as e:
        logger.warning("registry failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await register_in_registry()
    yield


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def check_token(request: Request, call_next: Any) -> Response:
    if request.url.path in ("/.well-known/agent-card.json", "/metrics"):
        response: Response = await call_next(request)
        return response

    trace_id = request.headers.get("x-trace-id", "") 
    trace_id_var.set(trace_id)

    auth_header = request.headers.get("authorization", "")
    token = auth_header.removeprefix("Bearer ")

    try:
        verify_token(token)
    except jwt.InvalidTokenError:
        return JSONResponse(status_code=401, content={"detail": "Invalid or missing token"})

    response = await call_next(request)
    return response


def main() -> None:
    setup_logging()
    setup_tracing("calendar booker")

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    Instrumentator().instrument(app).expose(app)

    executor = CalendarBooker(settings.calendar_mcp_url, settings.anthropic_api_key)
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
    uvicorn.run(app, host="127.0.0.1", port=10000)


if __name__ == "__main__":
    main()
