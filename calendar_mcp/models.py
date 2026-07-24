from datetime import datetime

from uuid import UUID, uuid4
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Interview(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    candidate_id: UUID
    scheduled_at: datetime
    status: Literal["booked", "cancelled"] = "booked"

    @field_validator("scheduled_at")
    @classmethod
    def must_be_future(cls, value: datetime) -> datetime:
        if value <= datetime.now():
            raise ValueError("scheduled_at must be in the future")
        return value
