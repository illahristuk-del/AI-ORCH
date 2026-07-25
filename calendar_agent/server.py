import uvicorn
import httpx
import secrets

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from a2a.server.tasks import InMemoryTaskStore
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from calendar_agent.card import AGENT_CARD, BOOK_SKILLS, AGENT_ID
from calendar_agent.executor import CalendarBooker
from search_mcp.adapters.config import settings


async def register_in_registry() -> None:
    payload = {
        "id": AGENT_ID,
        "name": "calendar_booker",
        "description": BOOK_SKILLS.description,
        "skills": list(BOOK_SKILLS.tags),
        "url": settings.calendar_agent_url,
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
async def check_token(request: Request, call_next):
    if request.url.path == "/.well-known/agent-card.json":
        return await call_next(request)

    expected = f"Bearer {settings.agent_token}"
    if not secrets.compare_digest(request.headers.get("authorization", ""), expected):
        return JSONResponse(
            status_code=401, content={"detail": "Invalid token or missing token"}
        )
    return await call_next(request)


def main() -> None:
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
