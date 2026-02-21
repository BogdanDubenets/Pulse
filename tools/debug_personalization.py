
import asyncio
from sqlalchemy import select
from database.connection import AsyncSessionLocal
from database.models import User, UserSubscription, Channel, Story, Publication
from sqlalchemy.orm import selectinload

async def diagnose_users():
    async with AsyncSessionLocal() as session:
        # 1. Список користувачів
        print("=== Users ===")
        users_res = await session.execute(select(User))
        users = users_res.scalars().all()
        for u in users:
            print(f"ID: {u.id}, Name: {u.first_name}, Username: {u.username}")

        # 2. Підписки
        print("\n=== Subscriptions ===")
        subs_res = await session.execute(
            select(UserSubscription)
            .options(selectinload(UserSubscription.channel))
        )
        subs = subs_res.scalars().all()
        user_subs = {}
        for s in subs:
            if s.user_id not in user_subs:
                user_subs[s.user_id] = []
            user_subs[s.user_id].append(s.channel.title if s.channel else f"Unknown ({s.channel_id})")
        
        for u_id, channels in user_subs.items():
            print(f"User {u_id} follows: {', '.join(channels)}")

        # 3. Останні новини
        print("\n=== Recent Stories (Last 24h) ===")
        from datetime import datetime, timedelta, timezone
        threshold = datetime.now(timezone.utc) - timedelta(hours=24)
        stories_res = await session.execute(
            select(Story)
            .where(Story.last_updated_at >= threshold)
            .limit(5)
        )
        stories = stories_res.scalars().all()
        for s in stories:
            print(f"Story {s.id}: {s.title[:50]}... (Status: {s.status})")

if __name__ == "__main__":
    asyncio.run(diagnose_users())
