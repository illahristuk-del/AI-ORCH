import asyncio
from uuid import uuid4

import httpx
from a2a.client import ClientConfig, create_client
from a2a.types import Message, Part, Role, SendMessageRequest

from search_mcp.adapters.auth import create_token


async def main() -> None:
    try:
        token = create_token("check_client")
        http = httpx.AsyncClient(timeout=120, headers={"Authorization": f"Bearer {token}"})
        config = ClientConfig(httpx_client=http)
        client = await create_client("http://localhost:11000/", client_config=config)

        part = Part()
        part.text = "find a python developer with sql and book an interview for 2034-01-01 at 03:00"
        message = Message()
        message.message_id = str(uuid4())
        message.role = Role.ROLE_USER
        message.parts.append(part)

        request = SendMessageRequest(message=message)

        async for response in client.send_message(request):
            print(response)
    except Exception as e:
        print("TYPE:", type(e).__name__)
        print("ERROR:", e)
        print("DATA:", getattr(e, "data", None))
    finally:
        await http.aclose()


asyncio.run(main())
