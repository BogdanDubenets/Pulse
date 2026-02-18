
import asyncio
from database.connection import engine
from sqlalchemy import text

async def add_category_column():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE publications ADD COLUMN category VARCHAR;"))
            print("Column 'category' added to 'publications' table.")
        except Exception as e:
            print(f"Error (maybe column already exists?): {e}")

if __name__ == "__main__":
    asyncio.run(add_category_column())
