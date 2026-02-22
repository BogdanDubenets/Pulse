import asyncio
import sys
import os

# Додаємо кореневу директорію до path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database.connection import AsyncSessionLocal
from loguru import logger

async def migrate():
    logger.info("Впровадження схеми для Каталогу та Аукціонів...")
    async with AsyncSessionLocal() as session:
        try:
            # 1. Update Channels table
            logger.info("Оновлення таблиці channels...")
            await session.execute(text("ALTER TABLE channels ADD COLUMN IF NOT EXISTS is_core BOOLEAN DEFAULT FALSE;"))
            await session.execute(text("ALTER TABLE channels ADD COLUMN IF NOT EXISTS partner_status VARCHAR DEFAULT 'organic';"))
            await session.execute(text("ALTER TABLE channels ADD COLUMN IF NOT EXISTS pinned_msg_id BIGINT;"))
            await session.execute(text("ALTER TABLE channels ADD COLUMN IF NOT EXISTS posts_count_24h INTEGER DEFAULT 0;"))

            # 2. Update Users table
            logger.info("Оновлення таблиці users...")
            await session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR DEFAULT 'demo';"))
            await session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_expires_at TIMESTAMP WITH TIME ZONE;"))

            # 3. Update User Subscriptions table
            logger.info("Оновлення таблиці user_subscriptions...")
            await session.execute(text("ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS last_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();"))

            # 4. Create Auctions table
            logger.info("Створення таблиці auctions...")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS auctions (
                    id SERIAL PRIMARY KEY,
                    category VARCHAR NOT NULL,
                    current_bid INTEGER DEFAULT 0,
                    leader_user_id BIGINT,
                    channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
                    ends_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """))
            await session.execute(text("CREATE INDEX IF NOT EXISTS ix_auctions_category ON auctions(category);"))

            await session.commit()
            logger.info("Міграція завершена успішно!")
        except Exception as e:
            logger.error(f"Помилка міграції: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(migrate())
