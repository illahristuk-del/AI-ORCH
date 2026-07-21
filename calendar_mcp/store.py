from typing import Protocol

from .models import Interview


class CalendarRepository(Protocol):
    async def book(self, interview: Interview) -> Interview: ...
