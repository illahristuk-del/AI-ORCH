from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class AuditEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.now)
    actor: str = Field(min_length=1, max_length=100)
    action: str = Field(min_length=1, max_length=100)
    resource: str | None = Field(default=None, max_length=200)
    status: str = Field(min_length=1, max_length=50)
    details: str | None = Field(default=None, max_length=1000)
