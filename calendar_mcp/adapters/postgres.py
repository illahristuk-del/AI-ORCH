from sqlalchemy.ext.asyncio import AsyncSession

from calendar_mcp.adapters.orm import InterviewOrmModel
from calendar_mcp.models import Interview


class PostgresCalendarRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def book(self, interview: Interview) -> Interview:
        booking = InterviewOrmModel(
            id=interview.id,
            candidate_id=interview.candidate_id,
            scheduled_at=interview.scheduled_at,
            status=interview.status,
        )

        self._session.add(booking)
        await self._session.commit()
        return interview
