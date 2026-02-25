import asyncio
from sqlalchemy import text
from database.connection import AsyncSessionLocal
from loguru import logger

async def migrate():
    logger.info("Starting database migration...")
    async with AsyncSessionLocal() as session:
        try:
            # 1. Check current vector dimension (optional, just force update)
            # We drop and add column to be safe and clear data
            logger.info("Dropping old embedding_vector column...")
            await session.execute(text("ALTER TABLE stories DROP COLUMN IF EXISTS embedding_vector;"))
            
            logger.info("Adding new embedding_vector column (768)...")
            await session.execute(text("ALTER TABLE stories ADD COLUMN embedding_vector vector(768);"))
            
            await session.commit()
            logger.info("Migration successful! vector(768) applied.")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(migrate())
