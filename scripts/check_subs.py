import asyncio
from database.connection import AsyncSessionLocal
from database.models import UserSubscription, Channel
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as s:
        r = await s.execute(select(UserSubscription).where(UserSubscription.user_id == 461874849))
        subs = r.scalars().all()
        print(f"Subscriptions for user 461874849: {len(subs)}")
        for sub in subs:
            ch = await s.get(Channel, sub.channel_id)
            title = ch.title if ch else "?"
            print(f"  - sub_id:{sub.id} | channel_id:{sub.channel_id} | {title} | created: {sub.created_at}")

asyncio.run(check())
