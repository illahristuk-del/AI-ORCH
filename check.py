import asyncio
from uuid import uuid4

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    params = StdioServerParameters(command="python", args=["-m", "search_mcp.server"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            for tool in tools.tools:
                print("NAME:", tool.name)
                print("DESCRIPTION:", tool.description)
                print("SCHEMA:", tool.inputSchema)

            result = await session.call_tool(
                "search_candidates", {"query": "python backend", "limit": 3}
            )
            print("SEARCH:", result.structuredContent)

            candidate_id = result.structuredContent["result"][0]["id"]

            good = await session.read_resource(f"candidate://{candidate_id}")
            print("GOOD:", good.contents[0].text)

            bad = await session.read_resource("candidate://banana")
            print("BAD:", bad.contents[0].text)

            missing = await session.read_resource(f"candidate://{uuid4()}")
            print("MISSING ID:", missing.contents[0].text)


asyncio.run(main())
