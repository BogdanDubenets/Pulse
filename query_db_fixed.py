import asyncio
import urllib.parse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

async def main():
    # URL provided from .env
    raw_pass = "2WSG/?XynHg.?8x"
    # urlencode password
    encoded_pass = urllib.parse.quote_plus(raw_pass)
    
    url = f"postgresql+asyncpg://postgres.irjqhaxbinyczgyfndzc:{encoded_pass}@aws-1-eu-west-1.pooler.supabase.com:6543/postgres?ssl=require"
    print("Trying SQLAlchemy...")
    engine = create_async_engine(url)
    try:
        async with AsyncSession(engine) as session:
            print("Connected...")
            res = await session.execute(text("""
                SELECT c.id, c.username, c.title, c.is_active, c.last_scanned_at, c.posts_count_24h 
                FROM channels c 
                JOIN user_subscriptions us ON c.id = us.channel_id 
                WHERE us.user_id = 461874849
            """))
            rows = res.fetchall()
            print(f"Found {len(rows)} rows:")
            for r in rows:
                print(r)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
