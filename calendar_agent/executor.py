import json

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam, TextBlock, ToolParam, ToolUseBlock
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


class CalendarBooker(AgentExecutor):
    def __init__(self, calendar_mcp_url: str, anthropic_api_key: str) -> None:
        self.calendar_mcp_url = calendar_mcp_url
        self._anthropic_api_key = anthropic_api_key

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        print("current_task: ", context.current_task)
        print("task_id: ", context.task_id)
        print("context_id: ", context.context_id)

        if context.task_id is None or context.context_id is None:
            raise ValueError("Task must be initialized before execution")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        try:
            query = context.get_user_input()

            tools: list[ToolParam] = [
                {
                    "name": "book_interview",
                    "description": "Book an interview for a candidate at a given time.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "candidate_id": {
                                "type": "string",
                                "description": "UUID of the candidate to book",
                            },
                            "scheduled_at": {
                                "type": "string",
                                "description": "interview datetime in ISO format, e.g. 2026-08-15T14:00:00",
                            },
                        },
                        "required": ["candidate_id", "scheduled_at"],
                    },
                }
            ]

            messages: list[MessageParam] = [{"role": "user", "content": query}]

            client = AsyncAnthropic(api_key=self._anthropic_api_key)
            response = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=messages,
                tools=tools,
            )

            print("STOP REASON:", response.stop_reason)
            print("CONTENT:", response.content)

            messages.append({"role": "assistant", "content": response.content})

            for block in response.content:
                if isinstance(block, ToolUseBlock):
                    async with streamable_http_client(self.calendar_mcp_url) as (
                        read,
                        write,
                        _,
                    ):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            result = await session.call_tool(block.name, block.input)
                            messages.append(
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "tool_result",
                                            "tool_use_id": block.id,
                                            "content": json.dumps(
                                                result.structuredContent
                                            ),
                                        }
                                    ],
                                }
                            )

            final_result = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=messages,
                tools=tools,
            )

            print("FINAL STOP:", final_result.stop_reason)
            print("FINAL CONTENT:", final_result.content)

            final_text = "".join(
                block.text
                for block in final_result.content
                if isinstance(block, TextBlock)
            )

            part = Part()
            part.text = final_text
            await updater.add_artifact([part], name="interview")
            await updater.complete()
        except Exception as e:
            error_part = Part()
            error_part.text = f"Booking failed: {e}"
            message = updater.new_agent_message([error_part])
            await updater.failed(message=message)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.task_id is None or context.context_id is None:
            raise ValueError("Task must be initialized before cancel")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.cancel()
