from datetime import datetime

from uuid import UUID, uuid4
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Interview(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    candidate_id: UUID
    scheduled_at: datetime
    status: Literal["booked", "cancelled"] = "booked"
