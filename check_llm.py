import asyncio

from anthropic import AsyncAnthropic

from search_mcp.adapters.config import settings


async def main() -> None:
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=100,
        messages=[{"role": "user", "content": "Say hello on 3 languages"}],
    )
    print("REPLY: ", response.content[0].text)


asyncio.run(main())
