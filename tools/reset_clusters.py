import asyncio
from sqlalchemy import update, delete
from database.connection import AsyncSessionLocal
from database.models import Publication, Story
from loguru import logger

async def repair_clusters():
    """
    Скидає всі сюжети та знімає прив'язку публікацій, щоб форсувати перекластеризацію
    з новими налаштуваннями (text-embedding-004 та поріг 0.15).
    """
    logger.info("Starting cluster repair...")
    
    async with AsyncSessionLocal() as session:
        # 1. Відв'язуємо всі публікації від історій
        logger.info("Unlinking all publications from stories...")
        await session.execute(
            update(Publication).values(story_id=None)
        )
        
        # 2. Видаляємо всі історії
        logger.info("Deleting all existing stories...")
        await session.execute(
            delete(Story)
        )
        
        await session.commit()
        logger.info("✅ Clusters reset successfully. Now run re-clustering.")

if __name__ == "__main__":
    asyncio.run(repair_clusters())
