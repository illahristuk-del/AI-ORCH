from typing import cast

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam, TextBlock, ToolParam, ToolUseBlock

from orchestrator.audit_client import log_event
from orchestrator.client import ask_agent
from orchestrator.registry_client import fetch_agents


class OrchestratorExecutor(AgentExecutor):
    def __init__(
        self, anthropic_api_key: str, registry_url: str, audit_url: str
    ) -> None:
        self._anthropic_api_key = anthropic_api_key
        self._registry_url = registry_url
        self._audit_url = audit_url

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.task_id is None or context.context_id is None:
            raise ValueError("Task must be initialized before execution")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        query = context.get_user_input()

        try:
            agents = await fetch_agents(self._registry_url)
            tools: list[ToolParam] = [
                {
                    "name": f"ask_{agent['name']}",
                    "description": agent["description"],
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "the task for this agent, in plain text",
                            },
                        },
                        "required": ["query"],
                    },
                }
                for agent in agents
            ]

            agent_urls = {f"ask_{agent['name']}": agent["url"] for agent in agents}

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
                        ok, result = await ask_agent(url, tool_input["query"])
                        await log_event(
                            audit_url=self._audit_url,
                            actor="orchestrator",
                            action="delegate",
                            resource=block.name,
                            status="completed" if ok else "failed",
                            details=tool_input["query"],
                        )
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
            import traceback

            traceback.print_exc()
            error_part = Part()
            error_part.text = f"Process failed: {e}"
            message = updater.new_agent_message([error_part])
            await updater.failed(message=message)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.task_id is None or context.context_id is None:
            raise ValueError("Task must be initialized before execution")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.cancel()
