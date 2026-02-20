
import asyncio
from database.connection import AsyncSessionLocal
from database.models import Publication, Story
from sqlalchemy import delete
from loguru import logger

async def reset_database():
    async with AsyncSessionLocal() as session:
        try:
            # Видаляємо всі публікації
            stmt_pubs = delete(Publication)
            result_pubs = await session.execute(stmt_pubs)
            
            # Видаляємо всі історії
            stmt_stories = delete(Story)
            result_stories = await session.execute(stmt_stories)
            
            await session.commit()
            logger.info(f"💥 Базу очищено! Видалено {result_pubs.rowcount} публікацій та {result_stories.rowcount} сюжетів.")
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Помилка при очищенні бази: {e}")

if __name__ == "__main__":
    asyncio.run(reset_database())
