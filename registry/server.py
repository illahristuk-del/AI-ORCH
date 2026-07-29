import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

import jwt
import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from registry.adapters.postgres import PostgresAgentRepository
from registry.models import Agent, AgentUpdate
from search_mcp.adapters.auth import verify_token
from search_mcp.adapters.db import make_engine, make_session_factory
from search_mcp.adapters.logging_config import setup_logging
from search_mcp.adapters.otel import setup_tracing

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = make_engine()
    app.state.session_factory = make_session_factory(engine)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory = request.app.state.session_factory
    async with factory() as session:
        yield session


def get_repo(session: AsyncSession = Depends(get_session)) -> PostgresAgentRepository:
    return PostgresAgentRepository(session)


async def require_token(authorization: str = Header(default="")) -> None:
    token = authorization.removeprefix("Bearer ")
    try:
        verify_token(token)
    except jwt.InvalidTokenError:
        logger.warning("rejected: invalid token")
        raise HTTPException(status_code=401, detail="Invalid token or missing token")


@app.get("/agents/search", status_code=200)
async def search_agent_by_skill(
    skill: str, repo: PostgresAgentRepository = Depends(get_repo)
) -> list[Agent]:
    return await repo.search_by_skill(skill)


@app.get("/agents", status_code=200)
async def get_list_agent(
    repo: PostgresAgentRepository = Depends(get_repo),
) -> list[Agent]:
    return await repo.get_all()


@app.get("/agents/{agent_id}", status_code=200)
async def get_agent(agent_id: UUID, repo: PostgresAgentRepository = Depends(get_repo)) -> Agent:
    agent = await repo.get(agent_id)
    if agent is None:
        logger.warning("agent not found")
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@app.post("/agents", status_code=201, dependencies=[Depends(require_token)])
async def create_agent(agent: Agent, repo: PostgresAgentRepository = Depends(get_repo)) -> Agent:
    return await repo.create(agent)


@app.patch("/agents/{agent_id}", dependencies=[Depends(require_token)])
async def patch_field_agent(
    agent_id: UUID, data: AgentUpdate, repo: PostgresAgentRepository = Depends(get_repo)
) -> Agent:
    agent = await repo.update(agent_id, data)
    if agent is None:
        logger.warning("agent not found")
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@app.delete("/agents/{agent_id}", status_code=204, dependencies=[Depends(require_token)])
async def delete_agent(agent_id: UUID, repo: PostgresAgentRepository = Depends(get_repo)) -> None:
    deleted = await repo.delete(agent_id)
    if not deleted:
        logger.warning("agent not found")
        raise HTTPException(status_code=404, detail="Agent not found")


def main() -> None:
    setup_logging()
    setup_tracing("registry server")

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()

    uvicorn.run(app, host="127.0.0.1", port=12000)


if __name__ == "__main__":
    main()
