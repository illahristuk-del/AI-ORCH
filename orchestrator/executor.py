from anthropic import AsyncAnthropic
from anthropic.types import MessageParam, TextBlock, ToolParam, ToolUseBlock

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part

from orchestrator.client import ask_agent

from typing import cast


class OrchestratorExecutor(AgentExecutor):
    def __init__(
        self, anthropic_api_key: str, hr_agent_url: str, calendar_agent_url: str
    ) -> None:
        self._anthropic_api_key = anthropic_api_key
        self._hr_agent_url = hr_agent_url
        self._calendar_agent_url = calendar_agent_url

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.task_id is None or context.context_id is None:
            raise ValueError("Task must be initialized before execution")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        query = context.get_user_input()

        try:
            tools: list[ToolParam] = [
                {
                    "name": "ask_hr_agent",
                    "description": "Search candidates by skills. Returns candidates WITH their IDs. Does NOT book interviews. "
                    "Returns IDs, does NOT book.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "what to search, e.g. 'python developers with sql'",
                            },
                        },
                        "required": ["query"],
                    },
                },
                {
                    "name": "ask_calendar_agent",
                    "description": "Book an interview for a candidate at a given time. Does NOT search candidates. "
                    "Needs the candidate ID and datetime in the query.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "booking task, e.g. 'book candidate cf7ca699 on 2026-09-01 at 15:00'",
                            },
                        },
                        "required": ["query"],
                    },
                },
            ]

            agent_urls = {
                "ask_hr_agent": self._hr_agent_url,
                "ask_calendar_agent": self._calendar_agent_url,
            }

            messages: list[MessageParam] = [{"role": "user", "content": query}]
            client = AsyncAnthropic(api_key=self._anthropic_api_key)

            while True:
                response = await client.messages.create(
                    model="claude-sonnet-4-6",
                    messages=messages,
                    max_tokens=1024,
                    tools=tools,
                )

                print("STOP REASON: ", response.stop_reason)
                print("CONTENT: ", response.content)

                messages.append({"role": "assistant", "content": response.content})
                if response.stop_reason != "tool_use":
                    break
                for block in response.content:
                    if isinstance(block, ToolUseBlock):
                        url = agent_urls[block.name]
                        tool_input = cast(dict[str, str], block.input)
                        result = await ask_agent(url, tool_input["query"])
                        messages.append(
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": result,
                                    }
                                ],
                            }
                        )

            final_text = "".join(
                block.text for block in response.content if isinstance(block, TextBlock)
            )

            part = Part()
            part.text = final_text
            await updater.add_artifact([part], name="orchestration_result")
            await updater.complete()
        except Exception as e:
            error_part = Part()
            error_part.text = f"Process failed: {e}"
            message = updater.new_agent_message([error_part])
            await updater.failed(message=message)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.task_id is None or context.context_id is None:
            raise ValueError("Task must be initialized before execution")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.cancel()
