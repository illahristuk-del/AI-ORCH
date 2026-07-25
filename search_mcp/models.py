from typing import Annotated
from uuid import UUID, uuid4

from annotated_types import Len
from pydantic import BaseModel, ConfigDict, Field


class Candidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=100)
    skills: Annotated[tuple[str, ...], Len(min_length=1)]
    experience_years: int = Field(ge=0, le=50)
