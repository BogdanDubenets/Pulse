import asyncio
from sqlalchemy import text
from database.connection import AsyncSessionLocal

async def migrate():
    print("Migrating database...")
    async with AsyncSessionLocal() as session:
        # Додаємо колонки, якщо їх немає
        queries = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS referrer_id BIGINT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS affiliate_earned_stars FLOAT DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS referrals_count INTEGER DEFAULT 0",
            "ALTER TABLE users ADD CONSTRAINT fk_referrer FOREIGN KEY (referrer_id) REFERENCES users(id) ON DELETE SET NULL"
        ]
        
        for q in queries:
            try:
                await session.execute(text(q))
                print(f"Executed: {q}")
            except Exception as e:
                print(f"Error executing {q}: {e}")
                
        await session.commit()
    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
