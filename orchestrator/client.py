import logging
from uuid import uuid4

import httpx
from a2a.client import ClientConfig, create_client
from a2a.types import Message, Part, Role, SendMessageRequest

from search_mcp.adapters.auth import create_token
from search_mcp.adapters.tracing import trace_id_var

logger = logging.getLogger(__name__)


async def ask_agent(agent_url: str, query: str) -> tuple[bool, str]:
    token = create_token("orchestrator")
    trace_id = trace_id_var.get()
    http = httpx.AsyncClient(timeout=60, headers={"Authorization": f"Bearer {token}", "X-Trace-Id": trace_id})
    try:
        config = ClientConfig(httpx_client=http)
        client = await create_client(agent_url, client_config=config)

        part = Part()
        part.text = query
        message = Message()
        message.message_id = str(uuid4())
        message.role = Role.ROLE_USER
        message.parts.append(part)
        request = SendMessageRequest(message=message)

        result_text = ""
        async for response in client.send_message(request):
            if response.HasField("task"):
                task = response.task
                for artifact in task.artifacts:
                    for response_part in artifact.parts:
                        if response_part.text:
                            result_text = response_part.text
        return True, result_text
    except Exception as e:
        logger.exception("agent call failed")
        return False, f"Agent call failed: {e}"
    finally:
        await http.aclose()
