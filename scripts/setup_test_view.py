
import asyncio
from database.connection import AsyncSessionLocal
from database.models import User, Channel, UserSubscription, Publication, Story
from sqlalchemy import select, func

async def setup_test_data():
    async with AsyncSessionLocal() as session:
        # 1. Check user
        user_id = 461874849
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            print(f"Creating user {user_id}")
            user = User(id=user_id, first_name="Test User", username="testuser")
            session.add(user)
        
        # 2. Get all channels
        result = await session.execute(select(Channel))
        channels = result.scalars().all()
        print(f"Found {len(channels)} channels")
        
        # 3. Subscribe user to all channels if not already
        for channel in channels:
            res_sub = await session.execute(
                select(UserSubscription).where(
                    UserSubscription.user_id == user_id,
                    UserSubscription.channel_id == channel.id
                )
            )
            if not res_sub.scalar_one_or_none():
                print(f"Subscribing user to {channel.title}")
                sub = UserSubscription(user_id=user_id, channel_id=channel.id)
                session.add(sub)
        
        # 4. Check publications count
        res_pubs = await session.execute(select(func.count(Publication.id)))
        print(f"Total publications: {res_pubs.scalar()}")

        # 5. Check stories count
        res_stories = await session.execute(select(func.count(Story.id)))
        print(f"Total stories: {res_stories.scalar()}")
        
        await session.commit()
        print("Setup complete")

if __name__ == "__main__":
    asyncio.run(setup_test_data())
