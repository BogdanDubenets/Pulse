import asyncio
from sqlalchemy import select
from database.connection import AsyncSessionLocal
from database.models import Publication, Channel

async def get_latest_truha():
    async with AsyncSessionLocal() as session:
        query = (
            select(Publication.content, Publication.published_at, Channel.title)
            .join(Channel)
            .where(Channel.title.like("%Труха%"))
            .order_by(Publication.published_at.desc())
            .limit(1)
        )
        result = await session.execute(query)
        p = result.first()
        if p:
            print(f"[{p[1]}] {p[2]}:")
            print("-" * 30)
            print(p[0])
            print("-" * 30)
        else:
            print("Публікацію не знайдено.")

if __name__ == "__main__":
    asyncio.run(get_latest_truha())
