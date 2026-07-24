from typing import Annotated
from uuid import UUID, uuid4

from annotated_types import Len
from pydantic import BaseModel, ConfigDict, Field


class Agent(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    skills: Annotated[tuple[str, ...], Len(min_length=1)]
    url: str


class AgentUpdate(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    skills: tuple[str, ...] | None = None
