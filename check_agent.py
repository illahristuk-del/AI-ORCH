import asyncio
import httpx

from uuid import uuid4
from a2a.client import create_client, ClientConfig
from a2a.types import Message, Part, Role, SendMessageRequest


async def main() -> None:
    try:
        http = httpx.AsyncClient(timeout=60)
        config = ClientConfig(httpx_client=http)
        client = await create_client(
            "http://localhost:9999/",
            client_config=config,
        )

        part = Part()
        part.text = "find python developers who have python and sql skills"

        message = Message()
        message.message_id = str(uuid4())
        message.role = Role.ROLE_USER
        message.parts.append(part)

        request = SendMessageRequest(message=message)

        async for response in client.send_message(request):
            print("---")
            print(response)
    except Exception as e:
        print("TYPE:", type(e).__name__)
        print("ERROR:", e)
        print("DATA:", getattr(e, "data", None))
    finally:
        await http.aclose()


asyncio.run(main())
