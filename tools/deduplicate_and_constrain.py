import asyncio
from sqlalchemy import text
from database.connection import AsyncSessionLocal

async def deduplicate_and_constrain():
    async with AsyncSessionLocal() as session:
        print("🛠️ Starting deduplication process...")
        
        # 1. Identify duplicates to keep (Min ID)
        print("🔍 Identifying duplicates to delete...")
        # We want to keep MIN(id) for each (channel_id, telegram_message_id)
        # So we delete rows where id is NOT in that set
        
        delete_query = text("""
            DELETE FROM publications
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM publications
                GROUP BY channel_id, telegram_message_id
            )
        """)
        
        try:
            result = await session.execute(delete_query)
            await session.commit()
            print(f"✅ Deleted {result.rowcount} duplicate rows.")
        except Exception as e:
            print(f"❌ Error deleting duplicates: {e}")
            return

        # 2. Add Unique Constraint
        print("🔒 Adding unique constraint 'uq_publications_channel_msg'...")
        try:
            await session.execute(text("""
                ALTER TABLE publications
                ADD CONSTRAINT uq_publications_channel_msg 
                UNIQUE (channel_id, telegram_message_id);
            """))
            await session.commit()
            print("✅ Unique constraint added successfully!")
        except Exception as e:
            if "already exists" in str(e):
                 print("ℹ️ Constraint already exists.")
            else:
                 print(f"❌ Error adding constraint: {e}")

if __name__ == "__main__":
    asyncio.run(deduplicate_and_constrain())
