import asyncio

from orchestrator.client import ask_agent


async def main() -> None:
    result = await ask_agent("http://localhost:9999/", "find python developers")
    print("HR RETURNED:", result)


asyncio.run(main())
