from .models import Candidate

CANDIDATES: list[Candidate] = [
    Candidate(
        name="Ivan Petrenko",
        skills=("python", "fastapi", "postgresql"),
        experience_years=4,
    ),
    Candidate(
        name="Olena Kovalchuk",
        skills=("python", "backend", "django", "postgresql"),
        experience_years=6,
    ),
    Candidate(
        name="Petro Shevchenko",
        skills=("java", "spring", "backend"),
        experience_years=3,
    ),
    Candidate(
        name="Maria Bondarenko",
        skills=("python", "asyncio", "backend"),
        experience_years=2,
    ),
    Candidate(
        name="Dmytro Tkachenko",
        skills=("go", "kubernetes", "docker"),
        experience_years=8,
    ),
    Candidate(
        name="Sofia Melnyk",
        skills=("typescript", "react", "frontend"),
        experience_years=5,
    ),
    Candidate(
        name="Andriy Kravets",
        skills=("python", "go", "kubernetes", "backend"),
        experience_years=7,
    ),
    Candidate(name="Yulia Lysenko", skills=("rust", "systems"), experience_years=3),
]
