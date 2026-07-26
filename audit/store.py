from typing import Protocol

from .models import AuditEvent


class AuditRepository(Protocol):
    async def create(self, event: AuditEvent) -> AuditEvent: ...

    async def get_all(self) -> list[AuditEvent]: ...
