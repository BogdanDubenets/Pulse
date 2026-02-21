import asyncio
from sqlalchemy import text
from database.connection import AsyncSessionLocal

async def fix_vector_dimension():
    async with AsyncSessionLocal() as session:
        # 1. Check current dimension
        print("Checking current vector dimension...")
        result = await session.execute(text(
            "SELECT atttypmod FROM pg_attribute WHERE attrelid = 'stories'::regclass AND attname = 'embedding_vector';"
        ))
        val = result.scalar()
        print(f"Current atttypmod: {val}")
        
        # atttypmod for vector(N) is usually N (or related to N). 
        # For 3072 it might be different, but let's see.
        
        # 2. Force migration
        print("Attempting to ALTER column to vector(768)...")
        try:
            await session.execute(text("ALTER TABLE stories ALTER COLUMN embedding_vector TYPE vector(768);"))
            await session.commit()
            print("✅ Migration successful!")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            
        # 3. Verify again
        result = await session.execute(text(
            "SELECT atttypmod FROM pg_attribute WHERE attrelid = 'stories'::regclass AND attname = 'embedding_vector';"
        ))
        print(f"New atttypmod: {result.scalar()}")

if __name__ == "__main__":
    asyncio.run(fix_vector_dimension())
