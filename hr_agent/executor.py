import json

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part

from search_mcp.store import CandidateRepository

LIMIT = 5


class HRRecruiterExecutor(AgentExecutor):
    def __init__(self, repo: CandidateRepository) -> None:
        self._repo = repo

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        print("INCOMING")
        print("current_task:", context.current_task)
        print("task_id:", context.task_id)
        print("context_id:", context.context_id)

        if context.task_id is None or context.context_id is None:
            raise ValueError("Task must be initialized before execution")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        try:
            query = context.get_user_input()
            results = await self._repo.search(query, LIMIT)
            part = Part()
            part.text = json.dumps([c.model_dump(mode="json") for c in results])
            await updater.add_artifact([part], name="candidates")
            await updater.complete()
        except Exception as e:
            error_part = Part()
            error_part.text = f"Search failed: {e}"
            message = updater.new_agent_message([error_part])
            await updater.failed(message=message)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.task_id is None or context.context_id is None:
            raise ValueError("Task must be initialized before cancel")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.cancel()
