import asyncio
from services.monitor import monitor
from database.connection import AsyncSessionLocal
from database.models import Publication
from sqlalchemy import select, func
from loguru import logger
import sys
import os

async def test_monitor():
    logger.info("Starting initial monitoring test...")
    
    try:
        # Стартуємо клієнт
        await monitor.start()
        
        # Запускаємо один цикл збору
        logger.info("Executing monitoring cycle...")
        await monitor.run_monitoring()
        
        # Перевіряємо результат у БД
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(func.count(Publication.id)))
            count = result.scalar()
            logger.info(f"Total publications collected: {count}")
            
            if count > 0:
                logger.info("News collection verified successfully!")
            else:
                logger.warning("No news collected. Check if channels have new posts.")
                
    except Exception as e:
        logger.error(f"Monitoring test failed: {e}")
    finally:
        await monitor.stop()

if __name__ == "__main__":
    sys.path.append(os.getcwd())
    asyncio.run(test_monitor())
