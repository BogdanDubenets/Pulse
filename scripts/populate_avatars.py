import asyncio
from sqlalchemy import select
from database.connection import AsyncSessionLocal
from database.models import Channel
from loguru import logger

async def populate_avatars():
    logger.info("Populating avatars for existing channels...")
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(Channel).where(Channel.avatar_url == None)
            result = await session.execute(stmt)
            channels = result.scalars().all()
            
            logger.info(f"Found {len(channels)} channels without avatars.")
            
            for ch in channels:
                ch.avatar_url = f"/api/v1/catalog/photo/{ch.telegram_id}"
                logger.info(f"Set avatar for channel {ch.title} (@{ch.username})")
            
            await session.commit()
            logger.info("Avatar population successful!")
        except Exception as e:
            logger.error(f"Failed to populate avatars: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(populate_avatars())
