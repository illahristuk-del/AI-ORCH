import asyncio
from uuid import uuid4

import httpx
from a2a.client import ClientConfig, create_client
from a2a.types import Message, Part, Role, SendMessageRequest


async def main() -> None:
    try:
        http = httpx.AsyncClient(timeout=60)
        config = ClientConfig(httpx_client=http)
        client = await create_client(
            "http://localhost:10000/",
            client_config=config,
        )

        part = Part()
        part.text = (
            "book an interview for candidate "
            "cf7ca699-a667-4e00-bc46-5016f889c336 on 2026-09-01 at 15:00"
        )

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
