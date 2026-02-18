import os
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
from database.connection import DATABASE_URL
from database.models import Base, Channel
import sys
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

# Очікуємо CLOUD_DATABASE_URL в .env
# Схема: postgresql+asyncpg://postgres:[password]@[host]:5432/postgres
CLOUD_URL = os.getenv("CLOUD_DATABASE_URL")

async def migrate():
    if not CLOUD_URL:
        logger.error("❌ CLOUD_DATABASE_URL не знайдено в .env")
        return

    logger.info("📡 Початок міграції в Supabase Cloud...")
    
    # 1. Створення структури
    try:
        cloud_engine = create_async_engine(CLOUD_URL)
        async with cloud_engine.begin() as conn:
            # Активуємо pgvector якщо треба
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            # Створюємо таблиці
            await Base.metadata.create_all(conn)
        logger.info("✅ Структуру бази даних створено.")
    except Exception as e:
        logger.error(f"❌ Помилка при створенні структури: {e}")
        return

    # 2. Перенесення каналів (якщо локальна база не порожня)
    try:
        from database.connection import AsyncSessionLocal
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as local_session:
            stmt = select(Channel)
            result = await local_session.execute(stmt)
            channels = result.scalars().all()
            
            if channels:
                from sqlalchemy.ext.asyncio import async_sessionmaker
                CloudSession = async_sessionmaker(cloud_engine, expire_on_commit=False)
                
                async with CloudSession() as cloud_session:
                    for ch in channels:
                        new_ch = Channel(
                            telegram_id=ch.telegram_id,
                            username=ch.username,
                            title=ch.title,
                            category=ch.category,
                            credibility_score=ch.credibility_score,
                            is_active=ch.is_active
                        )
                        cloud_session.add(new_ch)
                    await cloud_session.commit()
                logger.info(f"✅ Перенесено {len(channels)} каналів.")
            else:
                logger.info("ℹ️ Локальна база каналів порожня, перенесення даних пропущено.")
                
    except Exception as e:
        logger.warning(f"⚠️ Попередження при перенесенні даних: {e}")

    logger.info("🚀 Міграція завершена успішно!")

if __name__ == "__main__":
    asyncio.run(migrate())
