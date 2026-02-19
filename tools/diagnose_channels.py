import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import ssl

DATABASE_URL = "postgresql+asyncpg://postgres.irjqhaxbinyczgyfndzc:2WSG/?XynHg.?8x@aws-1-eu-west-1.pooler.supabase.com:6543/postgres"

async def diagnose():
    connect_args = {}
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ctx
    connect_args["prepared_statement_cache_size"] = 0
    connect_args["statement_cache_size"] = 0

    engine = create_async_engine(DATABASE_URL, connect_args=connect_args)
    
    async with engine.connect() as conn:
        print("--- Канали ---")
        result = await conn.execute(text("SELECT id, title, telegram_id, is_active, username FROM channels WHERE id IN (11, 13)"))
        for row in result:
            print(f"ID: {row.id} | Title: {row.title} | TG ID: {row.telegram_id} | Active: {row.is_active} | Username: {row.username}")
        
        print("\n--- Підписки ---")
        result = await conn.execute(text("SELECT * FROM user_subscriptions WHERE channel_id IN (11, 13)"))
        for row in result:
            print(f"Sub ID: {row.id} | User: {row.user_id} | Channel: {row.channel_id}")

        print("\n--- Останні публікації для кожного каналу ---")
        for cid in [11, 13]:
            count = await conn.scalar(text(f"SELECT count(*) FROM publications WHERE channel_id = {cid}"))
            last = await conn.scalar(text(f"SELECT created_at FROM publications WHERE channel_id = {cid} ORDER BY created_at DESC LIMIT 1"))
            print(f"Channel {cid}: Total {count} pubs. Last at: {last}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(diagnose())
