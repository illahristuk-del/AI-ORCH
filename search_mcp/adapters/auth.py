from datetime import UTC, datetime, timedelta

import jwt

from search_mcp.adapters.config import settings


def create_token(actor: str) -> str:
    payload = {
        "sub": actor,
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=30),
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def verify_token(token: str) -> str:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    sub: str = payload["sub"]
    return sub
