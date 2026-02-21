
import asyncio
from sqlalchemy import select, func
from database.connection import create_async_engine, async_sessionmaker, AsyncSession
from database.models import Publication, Story
import os

async def check_online():
    # Використовуємо хмарну URL
    url = "postgresql+asyncpg://postgres.irjqhaxbinyczgyfndzc:2WSG/?XynHg.?8x@aws-1-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
    engine = create_async_engine(url, connect_args={"ssl": False} if "sslmode=require" not in url else {}) # Simplified for check
    # Actually, connection.py logic is better. Let's just import it if we can override.
    
    from database.connection import AsyncSessionLocal
    # We'll just trust the env var we set in the previous tool call if it persists, 
    # but tool calls are stateless. I'll just run a command that checks it.
    pass

if __name__ == "__main__":
    # Better yet, just run a one-liner command
    pass
