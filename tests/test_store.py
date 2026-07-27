from uuid import uuid4

from search_mcp.models import Candidate
from search_mcp.store import InMemoryCandidateRepository, rank_candidates


def _repo(*candidates: Candidate) -> InMemoryCandidateRepository:
    return InMemoryCandidateRepository(list(candidates))


def test_search_ranks_by_match_count() -> None:
    weak = Candidate(name="weak", skills=("python",), experience_years=10)
    strong = Candidate(name="strong", skills=("python", "docker"), experience_years=1)

    result = rank_candidates([weak, strong], "python docker", limit=5)

    assert [c.name for c in result] == ["strong", "weak"]


def test_search_breaks_ties_by_experience() -> None:
    junior = Candidate(name="Junior", skills=("python", "SQL"), experience_years=1)
    middle = Candidate(
        name="Middle", skills=("python", "SQL", "Docker", "NoSql"), experience_years=3
    )
    senior = Candidate(
        name="Senior",
        skills=("python", "SQL", "Docker", "NoSql", "AWS", "Kubernetes", "Redis"),
        experience_years=6,
    )

    result = rank_candidates([junior, middle, senior], "python SQL", limit=5)

    assert [c.name for c in result] == ["Senior", "Middle", "Junior"]


def test_search_excludes_non_matching() -> None:
    not_match_candidate = Candidate(name="Karl", skills=("python",), experience_years=5)
    match_candidate = Candidate(name="John", skills=("java",), experience_years=5)

    result = rank_candidates([not_match_candidate, match_candidate], "java", limit=5)

    assert [c.name for c in result] == ["John"]


def test_search_returns_empty_when_nothing_matches() -> None:
    not_match_candidate1 = Candidate(name="Karl", skills=("python",), experience_years=5)
    not_match_candidate2 = Candidate(name="Bob", skills=("tensorflow",), experience_years=5)
    not_match_candidate3 = Candidate(name="Derek", skills=("go",), experience_years=5)

    result = rank_candidates(
        [not_match_candidate1, not_match_candidate2, not_match_candidate3],
        "java",
        limit=5,
    )

    assert result == []


def test_search_respects_limit() -> None:
    junior = Candidate(name="Junior", skills=("python", "SQL"), experience_years=1)
    middle = Candidate(
        name="Middle", skills=("python", "SQL", "Docker", "NoSql"), experience_years=3
    )
    senior = Candidate(
        name="Senior",
        skills=("python", "SQL", "Docker", "NoSql", "AWS", "Kubernetes", "Redis"),
        experience_years=6,
    )

    result = rank_candidates([junior, middle, senior], "python SQL", limit=1)

    assert [c.name for c in result] == ["Senior"]


async def test_get_returns_candidate_by_id() -> None:
    karl = Candidate(name="Karl", skills=("python",), experience_years=1)
    repo = _repo(karl)

    result = await repo.get(karl.id)

    assert result == karl


async def test_get_returns_none_for_unknown_id() -> None:
    karl = Candidate(name="Karl", skills=("python",), experience_years=1)
    repo = _repo(karl)

    result = await repo.get(uuid4())

    assert result is None


def test_search_normalizes_skill_case() -> None:
    karl = Candidate(name="Karl", skills=("PYTHON",), experience_years=1)

    result = rank_candidates([karl], "python", limit=1)

    assert [c.name for c in result] == ["Karl"]


def test_search_normalizes_query_case() -> None:
    karl = Candidate(name="Karl", skills=("python",), experience_years=1)

    result = rank_candidates([karl], "PYTHON", limit=1)

    assert [c.name for c in result] == ["Karl"]
