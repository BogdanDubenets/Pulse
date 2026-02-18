import asyncio
from database.connection import AsyncSessionLocal
from database.models import Channel
from sqlalchemy import select

async def fix():
    async with AsyncSessionLocal() as s:
        result = await s.execute(select(Channel).where(Channel.title.ilike("%Труха%")))
        ch = result.scalar_one_or_none()
        if ch:
            print(f"Found: {ch.title} | category was: {ch.category}")
            ch.category = "Регіональні: Київ і область"
            await s.commit()
            print(f"Updated to: {ch.category}")
        else:
            print("Channel not found")

asyncio.run(fix())
