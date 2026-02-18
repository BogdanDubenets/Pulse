
import asyncio
from database.connection import AsyncSessionLocal
from database.models import User, Channel, UserSubscription, Publication, Story
from sqlalchemy import select, func

async def debug_db():
    async with AsyncSessionLocal() as session:
        # 1. Total counts
        res_stories = await session.execute(select(func.count(Story.id)))
        res_pubs = await session.execute(select(func.count(Publication.id)))
        print(f"Total Stories in DB: {res_stories.scalar()}")
        print(f"Total Publications in DB: {res_pubs.scalar()}")

        # 2. Check stories and their publications
        stmt = select(Story)
        stories = (await session.execute(stmt)).scalars().all()
        for s in stories:
            p_count = await session.execute(select(func.count(Publication.id)).where(Publication.story_id == s.id))
            print(f"Story ID {s.id}: Title='{s.title}', Category='{s.category}', Status='{s.status}', Pubs count={p_count.scalar()}")

        # 3. Check publications without stories
        res_no_story = await session.execute(select(func.count(Publication.id)).where(Publication.story_id == None))
        print(f"Publications without story: {res_no_story.scalar()}")

        # 4. Check user subscriptions
        user_id = 461874849
        stmt_subs = select(UserSubscription).where(UserSubscription.user_id == user_id)
        subs = (await session.execute(stmt_subs)).scalars().all()
        print(f"User {user_id} subscriptions count: {len(subs)}")
        
if __name__ == "__main__":
    asyncio.run(debug_db())
