import asyncio
from sqlalchemy import text
from database.connection import AsyncSessionLocal

async def check_unclustered():
    async with AsyncSessionLocal() as session:
        print("🕵️ Checking for unclustered publications...")
        result = await session.execute(text("""
            SELECT COUNT(*) 
            FROM publications 
            WHERE story_id IS NULL;
        """))
        count = result.scalar()
        print(f"📉 Found {count} publications without a story.")
        
        if count > 0:
            print("   (These might need re-processing)")

if __name__ == "__main__":
    asyncio.run(check_unclustered())
