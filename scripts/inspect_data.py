
import asyncio
from database.connection import AsyncSessionLocal
from database.models import User, Channel, UserSubscription, Publication, Story
from sqlalchemy import select, func

async def inspect_channels_and_subs():
    async with AsyncSessionLocal() as session:
        # 1. List all channels
        res_ch = await session.execute(select(Channel))
        channels = res_ch.scalars().all()
        print("CHANNELS IN DB:")
        for c in channels:
            pub_count = await session.execute(select(func.count(Publication.id)).where(Publication.channel_id == c.id))
            print(f"ID {c.id}: {c.title} (Pubs: {pub_count.scalar()})")
        
        # 2. Check user subscriptions with details
        user_id = 461874849
        stmt_subs = select(UserSubscription).where(UserSubscription.user_id == user_id)
        subs = (await session.execute(stmt_subs)).scalars().all()
        print(f"\nUSER {user_id} SUBSCRIPTIONS:")
        for s in subs:
            ch = await session.get(Channel, s.channel_id)
            print(f"- {ch.title if ch else 'Unknown'} (ID: {s.channel_id})")

        # 3. Check which channels the 4 stories belong to
        print("\nSTORY DISTRIBUTION:")
        stories = (await session.execute(select(Story))).scalars().all()
        for s in stories:
            res_p = await session.execute(
                select(Channel.title, func.count(Publication.id))
                .join(Publication, Channel.id == Publication.channel_id)
                .where(Publication.story_id == s.id)
                .group_by(Channel.title)
            )
            dist = res_p.all()
            print(f"Story {s.id} ({s.title}): {dist}")

if __name__ == "__main__":
    asyncio.run(inspect_channels_and_subs())
