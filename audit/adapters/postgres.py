from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from audit.adapters.orm import AuditOrmModel
from audit.models import AuditEvent


class PostgresAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm_event: AuditOrmModel) -> AuditEvent:
        return AuditEvent(
            id=orm_event.id,
            timestamp=orm_event.timestamp,
            actor=orm_event.actor,
            action=orm_event.action,
            resource=orm_event.resource,
            status=orm_event.status,
            details=orm_event.details,
        )

    async def create(self, event: AuditEvent) -> AuditEvent:
        audit = AuditOrmModel(
            id=event.id,
            timestamp=event.timestamp,
            actor=event.actor,
            action=event.action,
            resource=event.resource,
            status=event.status,
            details=event.details,
        )

        self._session.add(audit)
        await self._session.commit()

        return event

    async def get_all(self) -> list[AuditEvent]:
        result = await self._session.execute(select(AuditOrmModel))
        rows = result.scalars().all()

        return [self._to_domain(row) for row in rows]
