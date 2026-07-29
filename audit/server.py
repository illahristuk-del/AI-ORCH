import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import jwt
import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator

from audit.adapters.postgres import PostgresAuditRepository
from audit.models import AuditEvent
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


async def get_repo(
    session: AsyncSession = Depends(get_session),
) -> PostgresAuditRepository:
    return PostgresAuditRepository(session)


async def require_token(authorization: str = Header(default="")) -> None:
    token = authorization.removeprefix("Bearer ")
    try:
        verify_token(token)
    except jwt.InvalidTokenError:
        logger.warning("rejected: invalid token")
        raise HTTPException(status_code=401, detail="Invalid token or missing token")


@app.get("/audit", status_code=200, dependencies=[Depends(require_token)])
async def get_all_audits(
    repo: PostgresAuditRepository = Depends(get_repo),
) -> list[AuditEvent]:
    return await repo.get_all()


@app.post("/audit", status_code=201, dependencies=[Depends(require_token)])
async def create_audit(
    event: AuditEvent, repo: PostgresAuditRepository = Depends(get_repo)
) -> AuditEvent:
    await repo.create(event)
    return event


def main() -> None:
    setup_logging()
    setup_tracing("audit")

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    Instrumentator().instrument(app).expose(app)

    uvicorn.run(app, host="127.0.0.1", port=13000)


if __name__ == "__main__":
    main()
