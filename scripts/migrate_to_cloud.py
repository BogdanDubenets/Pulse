import os
import asyncio
from sqlalchemy import create_engine, text, NullPool
from sqlalchemy.ext.asyncio import create_async_engine
from config.settings import config
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
    actual_url = CLOUD_URL
    if "@" in actual_url:
        from urllib.parse import quote_plus
        prefix, rest = actual_url.split("://", 1)
        auth, host_port_db = rest.rsplit("@", 1)
        if ":" in auth:
            user, password = auth.split(":", 1)
            auth = f"{user}:{quote_plus(password)}"
        actual_url = f"{prefix}://{auth}@{host_port_db}"

    if "sslmode=require" in actual_url:
        actual_url = actual_url.replace("sslmode=require", "ssl=require")
    
    masked_url = actual_url.split("@")[1] if "@" in actual_url else actual_url
    logger.info(f"🔗 Спроба підключення до: {masked_url}")
    
    try:
        cloud_engine = create_async_engine(
            actual_url, 
            connect_args={
                "statement_cache_size": 0,
                "prepared_statement_cache_size": 0
            },
            poolclass=NullPool
        )
        async with cloud_engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        if "Tenant or user not found" in str(e) and ":6543" in actual_url:
            logger.warning("🔄 Помилка транзакційного пулера. Пробую сесійний пулер (порт 5432)...")
            actual_url = actual_url.replace(":6543", ":5432")
            cloud_engine = create_async_engine(
                actual_url,
                connect_args={
                    "statement_cache_size": 0,
                    "prepared_statement_cache_size": 0
                },
                poolclass=NullPool
            )
            async with cloud_engine.begin() as conn:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                await conn.run_sync(Base.metadata.create_all)
        else:
            logger.error(f"❌ Помилка при створенні структури: {e}")
            return

    logger.info("✅ Структуру бази даних створено.")

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
