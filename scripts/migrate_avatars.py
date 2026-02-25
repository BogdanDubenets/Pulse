import asyncio
from sqlalchemy import text
from database.connection import AsyncSessionLocal
from loguru import logger

async def migrate():
    logger.info("Starting database migration for channel avatars...")
    async with AsyncSessionLocal() as session:
        try:
            # Add avatar_url column to channels table
            logger.info("Adding avatar_url column to channels...")
            await session.execute(text("ALTER TABLE channels ADD COLUMN IF NOT EXISTS avatar_url VARCHAR;"))
            
            await session.commit()
            logger.info("Migration successful! Column avatar_url added.")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(migrate())
