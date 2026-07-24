import asyncio
from orchestrator.registry_client import fetch_agents
from search_mcp.adapters.config import settings


async def main() -> None:
    agents = await fetch_agents(settings.registry_url)
    for agent in agents:
        print(agent)


asyncio.run(main())
