import asyncio
from sqlalchemy import select
from database.connection import AsyncSessionLocal
from database.models import Publication, Channel

async def get_pub_content():
    async with AsyncSessionLocal() as session:
        # Шукаємо останню публікацію Трухи
        query = (
            select(Publication.content, Publication.published_at, Channel.title)
            .join(Channel)
            .where(Channel.title.like("%Труха%"))
            .order_by(Publication.published_at.desc())
            .limit(1)
        )
        result = await session.execute(query)
        res = result.first()
        if res:
            content, date, title = res
            print("---")
            print(f"[{date}] {title}:")
            print(content)
            print("---")
        else:
            print("Публікацію не знайдено.")

if __name__ == "__main__":
    asyncio.run(get_pub_content())
