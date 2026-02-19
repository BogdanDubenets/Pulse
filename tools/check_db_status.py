import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import ssl

# Використовуємо хмарний URL
DATABASE_URL = "postgresql+asyncpg://postgres.irjqhaxbinyczgyfndzc:2WSG/?XynHg.?8x@aws-1-eu-west-1.pooler.supabase.com:6543/postgres"

async def check_news():
    connect_args = {}
    
    # SSL налаштування
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ctx
    
    # Налаштування для Pooler
    connect_args["prepared_statement_cache_size"] = 0
    connect_args["statement_cache_size"] = 0

    engine = create_async_engine(DATABASE_URL, connect_args=connect_args)
    
    async with engine.connect() as conn:
        # Перевірка користувачів
        user_count = await conn.scalar(text("SELECT count(*) FROM users"))
        print(f"Користувачів у базі: {user_count}")
        
        # Перевірка каналів
        channel_count = await conn.scalar(text("SELECT count(*) FROM channels"))
        print(f"Каналів у базі: {channel_count}")
        
        # Перевірка підписок
        sub_count = await conn.scalar(text("SELECT count(*) FROM user_subscriptions"))
        print(f"Підписок у базі: {sub_count}")
        
        # Перевірка публікацій
        pub_count = await conn.scalar(text("SELECT count(*) FROM publications"))
        print(f"Публікацій у базі: {pub_count}")
        
        if channel_count > 0:
            print("\nСтан каналів:")
            result = await conn.execute(text("SELECT title, username, last_scanned_at FROM channels LIMIT 5"))
            for row in result:
                print(f"- {row.title} (@{row.username}): Scanned at {row.last_scanned_at}")
        
        if pub_count > 0:
            print("\nОстанні 3 новини:")
            result = await conn.execute(text("SELECT content, created_at FROM publications ORDER BY created_at DESC LIMIT 3"))
            for row in result:
                print(f"[{row.created_at}] {str(row.content)[:100]}...")
        else:
            print("\nНовин поки немає.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_news())
