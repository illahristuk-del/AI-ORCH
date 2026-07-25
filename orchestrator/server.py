import secrets

import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from orchestrator.card import ORCHESTRATOR_CARD
from orchestrator.executor import OrchestratorExecutor
from search_mcp.adapters.config import settings

app = FastAPI()


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
    executor = OrchestratorExecutor(
        settings.anthropic_api_key,
        settings.registry_url,
    )

    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        agent_card=ORCHESTRATOR_CARD,
    )

    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(ORCHESTRATOR_CARD),
        jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url="/"),
    )

    uvicorn.run(app, host="127.0.0.1", port=11000)


if __name__ == "__main__":
    main()
