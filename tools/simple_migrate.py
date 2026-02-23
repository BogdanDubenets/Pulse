import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv
import ssl

load_dotenv()

async def migrate():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("Error: DATABASE_URL not found in .env")
        return

    connect_args = {}
    if "?sslmode=require" in url:
        url = url.replace("?sslmode=require", "")
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ctx

    if ":6543" in url:
        connect_args["prepared_statement_cache_size"] = 0
        connect_args["statement_cache_size"] = 0

    engine = create_async_engine(url, connect_args=connect_args)
    
    print(f"Connecting to database...")
    
    sql_commands = [
        "ALTER TABLE channels ADD COLUMN IF NOT EXISTS is_core BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE channels ADD COLUMN IF NOT EXISTS partner_status TEXT DEFAULT 'organic';",
        "ALTER TABLE channels ADD COLUMN IF NOT EXISTS partner_expires_at TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE channels ADD COLUMN IF NOT EXISTS pinned_msg_id BIGINT;",
        "ALTER TABLE channels ADD COLUMN IF NOT EXISTS posts_count_24h INTEGER DEFAULT 0;",
        "ALTER TABLE channels ADD COLUMN IF NOT EXISTS avatar_url TEXT;",
        
        """CREATE TABLE IF NOT EXISTS users (
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
        );""",
        
        "ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS position INTEGER DEFAULT 0;",
        "ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS last_changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;",
        
        """CREATE TABLE IF NOT EXISTS auctions (
            id SERIAL PRIMARY KEY,
            category TEXT,
            current_bid INTEGER DEFAULT 0,
            leader_user_id BIGINT,
            channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
            ends_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );""",
        
        "CREATE INDEX IF NOT EXISTS idx_auctions_category ON auctions(category);"
    ]
    
    async with engine.begin() as conn:
        for cmd in sql_commands:
            print(f"Executing: {cmd[:50]}...")
            await conn.execute(text(cmd))
    
    print("Migration finished successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
