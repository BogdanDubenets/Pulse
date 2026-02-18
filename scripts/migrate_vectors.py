import asyncio
from sqlalchemy import text
from database.connection import AsyncSessionLocal

async def migrate():
    try:
        async with AsyncSessionLocal() as session:
            print("Migrating stories table...")
            # Drop column
            await session.execute(text("ALTER TABLE stories DROP COLUMN IF EXISTS embedding_vector"))
            # Add column with 3072 dims
            await session.execute(text("ALTER TABLE stories ADD COLUMN embedding_vector vector(3072)"))
            await session.commit()
            print("Migration done. Stories table now has vector(3072).")
    except Exception as e:
        print(f"Migration error: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
