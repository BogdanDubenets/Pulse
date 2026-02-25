import asyncio
from database.connection import engine
from database.models import Base
from loguru import logger

async def init_db():
    async with engine.begin() as conn:
        logger.info("Initializing database tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
