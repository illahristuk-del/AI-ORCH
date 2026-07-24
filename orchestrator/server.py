import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from fastapi import FastAPI

from orchestrator.card import ORCHESTRATOR_CARD
from orchestrator.executor import OrchestratorExecutor
from search_mcp.adapters.config import settings


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

    app = FastAPI()

    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(ORCHESTRATOR_CARD),
        jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url="/"),
    )

    uvicorn.run(app, host="127.0.0.1", port=11000)


if __name__ == "__main__":
    main()
