import asyncio
import logging
import os
import sys

# Додаємо кореневу директорію до path, щоб імпорти працювали
sys.path.append(os.getcwd())

from sqlalchemy import select
from database.connection import AsyncSessionLocal
from database.models import Channel
from api.utils.storage import get_or_download_avatar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("warmup_photos")

async def warmup_photos():
    logger.info("Starting photo warmup for all active channels...")
    
    async with AsyncSessionLocal() as session:
        # Беремо всі активні канали
        stmt = select(Channel).where(Channel.is_active == True)
        result = await session.execute(stmt)
        channels = result.scalars().all()
        
        logger.info(f"Found {len(channels)} channels to process.")
        
        count = 0
        for ch in channels:
            logger.info(f"[{count+1}/{len(channels)}] Processing: {ch.title} (@{ch.username})")
            # Викликаємо нашу утиліту, яка сама перевірить диск і завантажить якщо треба
            path = await get_or_download_avatar(ch.telegram_id, username=ch.username)
            if path:
                count += 1
            
            # Невелика пауза, щоб не спамити Telegram API занадто швидко
            await asyncio.sleep(0.5)

    logger.info(f"Warmup finished! Successfully processed {count} photos.")

if __name__ == "__main__":
    asyncio.run(warmup_photos())
