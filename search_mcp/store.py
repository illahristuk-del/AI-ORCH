from typing import Protocol
from uuid import UUID

from .models import Candidate


class CandidateRepository(Protocol):
    async def get(self, candidate_id: UUID) -> Candidate | None: ...

    async def search(self, query: str, limit: int) -> list[Candidate]: ...


class InMemoryCandidateRepository:
    def __init__(self, candidates: list[Candidate]) -> None:
        self._candidates = list(candidates)

    async def get(self, candidate_id: UUID) -> Candidate | None:
        return next((c for c in self._candidates if c.id == candidate_id), None)

    async def search(self, query: str, limit: int) -> list[Candidate]:
        tokens = {t.strip(",.;") for t in query.lower().split()}
        scored: list[tuple[int, Candidate]] = []
        for candidate in self._candidates:
            skills = {s.lower() for s in candidate.skills}
            score = len(tokens & skills)
            if score > 0:
                scored.append((score, candidate))
        scored.sort(key=lambda pair: (pair[0], pair[1].experience_years), reverse=True)
        return [candidate for _, candidate in scored[:limit]]
