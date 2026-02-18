import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import select, text
from database.connection import AsyncSessionLocal, engine
from database.models import Base, User, UserSubscription


async def migrate_users():
    print("Starting migration: Users table...")
    
    # 1. Create table if not exists
    async with engine.begin() as conn:
        print("Creating table 'users'...")
        await conn.run_sync(Base.metadata.create_all)
        
    # 2. Backfill from user_subscriptions
    async with AsyncSessionLocal() as session:
        print("Backfilling users from existing subscriptions...")
        
        # Get distinct user_ids from subscriptions
        result = await session.execute(select(UserSubscription.user_id).distinct())
        user_ids = result.scalars().all()
        
        count = 0
        for uid in user_ids:
            # Check if user exists
            existing = await session.get(User, uid)
            if not existing:
                new_user = User(
                    id=uid,
                    first_name=f"User {uid}", # Placeholder
                    username=None,
                    morning_digest_time="08:00",
                    evening_digest_time="20:00",
                    is_active=True
                )
                session.add(new_user)
                count += 1
        
        await session.commit()
        print(f"Migration complete. Created {count} new users.")

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(migrate_users())
    except KeyboardInterrupt:
        pass
