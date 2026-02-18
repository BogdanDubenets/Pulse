import asyncio
from database.connection import AsyncSessionLocal
from database.models import Publication, Story
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta

async def check_stats():
    async with AsyncSessionLocal() as session:
        # Часовий поріг: остання година
        last_hour = datetime.utcnow() - timedelta(hours=1)
        
        # 1. Загальна кількість публікацій за останню годину
        stmt_count = select(func.count(Publication.id)).where(Publication.published_at >= last_hour)
        res_count = await session.execute(stmt_count)
        count = res_count.scalar()
        
        # 2. Останні 5 публікацій
        stmt_last = (
            select(Publication)
            .order_by(desc(Publication.published_at))
            .limit(5)
        )
        res_last = await session.execute(stmt_last)
        last_pubs = res_last.scalars().all()
        
        # 3. Кількість нових сюжетів (Stories) за останню годину
        stmt_stories = select(func.count(Story.id)).where(Story.last_updated_at >= last_hour)
        res_stories = await session.execute(stmt_stories)
        stories_count = res_stories.scalar()
        
        print("--- Pulse Database Stats ---")
        print(f"Publications in last hour: {count}")
        print(f"New Stories in last hour: {stories_count}")
        print("\nLast 5 items:")
        for p in last_pubs:
            print(f"- [{p.published_at}] {p.content[:60]}...")
            if p.story_id:
                print(f"  (linked to story: {p.story_id})")

if __name__ == "__main__":
    asyncio.run(check_stats())
