import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main() -> None:
    async with streamable_http_client("http://127.0.0.1:8001/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            for tool in tools.tools:
                print("TOOL:", tool.name)

            result = await session.call_tool(
                "book_interview",
                {
                    "candidate_id": "cf7ca699-a667-4e00-bc46-5016f889c336",
                    "scheduled_at": "2026-08-15T14:00:00",
                },
            )
            print("RESULT:", result.structuredContent)
            print("CONTENT:", result.content)


asyncio.run(main())
