import asyncio

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
                "search_candidates", {"query": "python backend"}
            )
            print("RESULT:", result)


asyncio.run(main())
