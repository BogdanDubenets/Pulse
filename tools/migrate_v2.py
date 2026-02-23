import asyncio
from sqlalchemy import text
from database.connection import AsyncSessionLocal
from loguru import logger

async def migrate():
    logger.info("Starting database migration v2 (Tiered System)...")
    async with AsyncSessionLocal() as session:
        try:
            # 1. Update CHANNELS table
            logger.info("Updating 'channels' table...")
            steps = [
                "ALTER TABLE channels ADD COLUMN IF NOT EXISTS is_core BOOLEAN DEFAULT FALSE;",
                "ALTER TABLE channels ADD COLUMN IF NOT EXISTS partner_status TEXT DEFAULT 'organic';",
                "ALTER TABLE channels ADD COLUMN IF NOT EXISTS partner_expires_at TIMESTAMP WITH TIME ZONE;",
                "ALTER TABLE channels ADD COLUMN IF NOT EXISTS pinned_msg_id BIGINT;",
                "ALTER TABLE channels ADD COLUMN IF NOT EXISTS posts_count_24h INTEGER DEFAULT 0;",
                "ALTER TABLE channels ADD COLUMN IF NOT EXISTS avatar_url TEXT;"
            ]
            for step in steps:
                await session.execute(text(step))
            
            # 2. Create USERS table
            logger.info("Creating 'users' table if not exists...")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    first_name TEXT,
                    username TEXT,
                    language_code TEXT DEFAULT 'uk',
                    morning_digest_time TEXT DEFAULT '08:00',
                    evening_digest_time TEXT DEFAULT '20:00',
                    is_active BOOLEAN DEFAULT TRUE,
                    subscription_tier TEXT DEFAULT 'demo',
                    subscription_expires_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))

            # 3. Update USER_SUBSCRIPTIONS table
            logger.info("Updating 'user_subscriptions' table...")
            await session.execute(text("ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS position INTEGER DEFAULT 0;"))
            await session.execute(text("ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS last_changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;"))

            # 4. Create AUCTIONS table
            logger.info("Creating 'auctions' table if not exists...")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS auctions (
                    id SERIAL PRIMARY KEY,
                    category TEXT,
                    current_bid INTEGER DEFAULT 0,
                    leader_user_id BIGINT,
                    channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
                    ends_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_auctions_category ON auctions(category);"))

            await session.commit()
            logger.info("Migration successful! All columns and tables are now in sync with models.py")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(migrate())
