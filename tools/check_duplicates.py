import asyncio
from sqlalchemy import text
from database.connection import AsyncSessionLocal

async def check_duplicates():
    async with AsyncSessionLocal() as session:
        print("🔎 Searching for duplicate publications...")
        
        query = text("""
            SELECT channel_id, telegram_message_id, COUNT(*) 
            FROM publications 
            GROUP BY channel_id, telegram_message_id 
            HAVING COUNT(*) > 1
        """)
        
        result = await session.execute(query)
        duplicates = result.fetchall()
        
        if not duplicates:
            print("✅ No duplicates found.")
        else:
            print(f"⚠️ Found {len(duplicates)} sets of duplicates:")
            for row in duplicates:
                print(f"   - Channel {row[0]}, Msg {row[1]}: {row[2]} copies")
                
            # Count total wasted rows
            total_waste = sum(row[2] - 1 for row in duplicates)
            print(f"🗑️ Total redundant rows to delete: {total_waste}")

if __name__ == "__main__":
    asyncio.run(check_duplicates())
