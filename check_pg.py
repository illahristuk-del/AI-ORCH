import asyncio

from sqlalchemy import text

from search_mcp.adapters.db import make_engine


async def main() -> None:
    engine = make_engine()
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print("DB OK:", result.scalar())
    await engine.dispose()


asyncio.run(main())
