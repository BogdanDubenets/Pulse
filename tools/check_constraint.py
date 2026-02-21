import asyncio
from sqlalchemy import text
from database.connection import AsyncSessionLocal

async def check_constraint():
    async with AsyncSessionLocal() as session:
        print("🕵️ Checking if constraint exists...")
        result = await session.execute(text("""
            SELECT conname
            FROM pg_constraint
            WHERE conname = 'uq_publications_channel_msg';
        """))
        if result.scalar():
            print("✅ Constraint 'uq_publications_channel_msg' FOUND.")
        else:
            print("❌ Constraint NOT found.")

if __name__ == "__main__":
    asyncio.run(check_constraint())
