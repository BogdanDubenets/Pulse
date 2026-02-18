import asyncio
from sqlalchemy import select, func
from database.connection import AsyncSessionLocal
from database.models import Channel, Publication, Story, UserSubscription

async def check_db_status():
    async with AsyncSessionLocal() as session:
        # Count Channels
        result = await session.execute(select(func.count(Channel.id)))
        channel_count = result.scalar()

        # Count Publications
        result = await session.execute(select(func.count(Publication.id)))
        publication_count = result.scalar()

        # Count Stories
        result = await session.execute(select(func.count(Story.id)))
        story_count = result.scalar()

        # Count Subscriptions
        result = await session.execute(select(func.count(UserSubscription.id)))
        subscription_count = result.scalar()

        print(f"📊 **Database Status**")
        print(f"- Channels monitored (total): {channel_count}")
        print(f"- User subscriptions: {subscription_count}")
        print(f"- Publications collected: {publication_count}")
        print(f"- Stories formed: {story_count}")

        # Get latest publication time
        if publication_count > 0:
            result = await session.execute(select(Publication.created_at).order_by(Publication.created_at.desc()).limit(1))
            latest_pub = result.scalar()
            print(f"- Latest publication: {latest_pub}")

if __name__ == "__main__":
    asyncio.run(check_db_status())
