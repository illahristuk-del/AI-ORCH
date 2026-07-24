from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from search_mcp.adapters.db import Base


class AgentOrmModel(Base):
    __tablename__ = "agents"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    skills: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
