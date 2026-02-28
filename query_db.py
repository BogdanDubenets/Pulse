import asyncio
import io
import os
import sys
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

async def main():
    load_dotenv()
    url = os.getenv('CLOUD_DATABASE_URL') or os.getenv('DATABASE_URL')
    if '?sslmode=require' in url:
        url = url.replace('?sslmode=require', '')
    print(f"URL: {url}")
    
    # Simple asyncpg directly to avoid verbose alchemy logs
    import asyncpg
    url = url.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(url)
    try:
        print("Connected...")
        query = """
        SELECT c.id, c.username, c.title, c.is_active, c.last_scanned_at, c.posts_count_24h 
        FROM channels c 
        JOIN user_subscriptions us ON c.id = us.channel_id 
        WHERE us.user_id = 461874849
        """
        rows = await conn.fetch(query)
        print(f"Found {len(rows)} rows:")
        for r in rows:
            print(dict(r))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
