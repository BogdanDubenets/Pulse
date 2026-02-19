import asyncio
from sqlalchemy import text
from database.connection import AsyncSessionLocal
import ssl

async def check_schema():
    connect_args = {"ssl": ssl.create_default_context()}
    connect_args["ssl"].check_hostname = False
    connect_args["ssl"].verify_mode = ssl.CERT_NONE
    
    engine = AsyncSessionLocal().bind
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT column_name, udt_name, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'stories' AND column_name = 'embedding_vector';
        """))
        row = result.fetchone()
        print(f"Column: {row[0]} | Type: {row[1]} | Length/Dim: {row[2]}")
        
        # Перевіримо розмірність через власну функцію pgvector якщо можливо
        try:
            dim = await conn.scalar(text("SELECT dimension(embedding_vector) FROM stories LIMIT 1"))
            print(f"Actual dimension from data: {dim}")
        except:
            print("Could not get dimension from data (table might be empty or function missing)")

if __name__ == "__main__":
    asyncio.run(check_schema())
