import asyncio
from sqlalchemy import select
from database.connection import AsyncSessionLocal
from database.models import Publication
from services.clustering import cluster_publication
from loguru import logger
import sys

async def process_stuck_publications():
    logger.info("Starting manual queue processing...")
    
    async with AsyncSessionLocal() as session:
        # Шукаємо всі публікації без story_id
        query = select(Publication).where(Publication.story_id == None)
        result = await session.execute(query)
        pubs = result.scalars().all()
        
        if not pubs:
            logger.info("No stuck publications found.")
            return

        logger.info(f"Found {len(pubs)} publications to process.")
        
        for pub in pubs:
            logger.info(f"Processing pub ID {pub.id}: {pub.content[:50]}...")
            try:
                # Викликаємо існуючу логіку кластеризації
                await cluster_publication(pub.id)
                logger.info(f"✅ Successfully processed pub {pub.id}")
            except Exception as e:
                logger.error(f"❌ Failed to process pub {pub.id}: {e}")
            
            # Невелике очікування, щоб не перевантажити API
            await asyncio.sleep(2)

    logger.info("Manual processing completed.")

if __name__ == "__main__":
    # Додаємо поточну директорію в path для імпортів
    import os
    sys.path.append(os.getcwd())
    asyncio.run(process_stuck_publications())
