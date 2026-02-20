
import asyncio
from database.connection import AsyncSessionLocal
from database.models import Publication, Story
from sqlalchemy import delete, select
from loguru import logger

AD_MARKERS = [
    "t.me/+", "t.me/joinchat", "#реклама", "#промо",
    "казино", "ставки", "заробіток", "промокод"
]

async def cleanup_ads():
    async with AsyncSessionLocal() as session:
        # 1. Знаходимо публікації з маркерами реклами
        total_deleted = 0
        for marker in AD_MARKERS:
            stmt = delete(Publication).where(Publication.content.ilike(f"%{marker}%"))
            result = await session.execute(stmt)
            total_deleted += result.rowcount
        
        await session.commit()
        logger.info(f"✅ Видалено {total_deleted} рекламних публікацій.")

        # 2. Видаляємо пусті історії (якщо такі залишились після роз'єднання)
        # В нашому новому режимі Stories все одно створюються 1 до 1, 
        # але старі пусті треба почистити.
        stmt_empty_stories = delete(Story).where(~Story.publications.any())
        result_stories = await session.execute(stmt_empty_stories)
        await session.commit()
        logger.info(f"✅ Видалено {result_stories.rowcount} порожніх історій.")

if __name__ == "__main__":
    asyncio.run(cleanup_ads())
