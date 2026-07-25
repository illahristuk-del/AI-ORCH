import httpx

from uuid import uuid4

from a2a.client import ClientConfig, create_client
from a2a.types import Message, Part, Role, SendMessageRequest

from search_mcp.adapters.config import settings


async def ask_agent(agent_url: str, query: str) -> str:
    headers = {"Authorization": f"Bearer {settings.agent_token}"}
    http = httpx.AsyncClient(timeout=60, headers=headers)
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
        return result_text
    except Exception as e:
        print("TYPE:", type(e).__name__)
        print("ERROR:", e)
        print("DATA:", getattr(e, "data", None))
        return f"Agent call failed: {e}"
    finally:
        await http.aclose()
