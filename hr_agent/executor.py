import json
import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam, TextBlock, ToolParam, ToolUseBlock
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from search_mcp.adapters.auth import create_token
from search_mcp.adapters.tracing import trace_id_var

logger = logging.getLogger(__name__)

system_config = "Always include each candidate's full UUID in your answer. Downstream agents need the ID to book interviews."


class HRRecruiterExecutor(AgentExecutor):
    def __init__(self, mcp_url: str, anthropic_api_key: str) -> None:
        self._mcp_url = mcp_url
        self._anthropic_api_key = anthropic_api_key

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.debug("current_task: %s", context.current_task)
        logger.debug("task_id: %s", context.task_id)
        logger.debug("context_id: %s", context.context_id)

        if context.task_id is None or context.context_id is None:
            raise ValueError("Task must be initialized before execution")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        try:
            query = context.get_user_input()

            tools: list[ToolParam] = [
                {
                    "name": "search_candidates",
                    "description": "Search for candidates by their technical skills.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "space-separated skills",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "max candidates",
                            },
                        },
                        "required": ["query"],
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
                system=system_config,
            )

            logger.debug("stop reason: %s", response.stop_reason)
            logger.debug("content: %s", response.content)

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                final = response
            else:
                for block in response.content:
                    if isinstance(block, ToolUseBlock):
                        token = create_token("hr_recruiter")
                        trace_id = trace_id_var.get()
                        async with streamablehttp_client(
                            self._mcp_url,
                            headers={
                                "Authorization": f"Bearer {token}",
                                "X-Trace-Id": trace_id,
                            },
                        ) as (
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
                                                "content": json.dumps(result.structuredContent),
                                            }
                                        ],
                                    }
                                )

                final = await client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1024,
                    messages=messages,
                    tools=tools,
                    system=system_config,
                )

            logger.debug("final stop: %s", final.stop_reason)
            logger.debug("final content: %s", final.content)

            final_text = "".join(
                block.text for block in final.content if isinstance(block, TextBlock)
            )

            part = Part()
            part.text = final_text
            await updater.add_artifact([part], name="candidates")
            await updater.complete()

        except Exception as e:
            logger.exception("hr recruiter search failed")
            error_part = Part()
            error_part.text = f"Search failed: {e}"
            message = updater.new_agent_message([error_part])
            await updater.failed(message=message)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.task_id is None or context.context_id is None:
            raise ValueError("Task must be initialized before cancel")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.cancel()
