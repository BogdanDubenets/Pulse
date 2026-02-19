import asyncio
from sqlalchemy import text
from database.connection import AsyncSessionLocal
from loguru import logger
import ssl

async def migrate_vector_dimension():
    logger.info("Migrating embedding_vector dimension to 768...")
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Видаляємо старий стовпець (або змінюємо тип)
            # В pgvector неможна просто змінити розмірність, треба перестворити стовпець
            await session.execute(text("ALTER TABLE stories DROP COLUMN IF EXISTS embedding_vector"))
            await session.execute(text("ALTER TABLE stories ADD COLUMN embedding_vector vector(768)"))
            
            await session.commit()
            logger.info("✅ Database migration successful: embedding_vector is now 768 dimensions.")
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(migrate_vector_dimension())
