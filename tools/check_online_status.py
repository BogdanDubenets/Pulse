import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import ssl

DATABASE_URL = "postgresql+asyncpg://postgres.irjqhaxbinyczgyfndzc:2WSG/?XynHg.?8x@aws-1-eu-west-1.pooler.supabase.com:6543/postgres"

async def check_online_status():
    connect_args = {"ssl": ssl.create_default_context()}
    connect_args["ssl"].check_hostname = False
    connect_args["ssl"].verify_mode = ssl.CERT_NONE
    connect_args["prepared_statement_cache_size"] = 0
    connect_args["statement_cache_size"] = 0

    engine = create_async_engine(DATABASE_URL, connect_args=connect_args)
    
    async with engine.connect() as conn:
        print("--- СТАНИ МОНІТОРИНГУ (за останні 24 год) ---")
        # Перевіримо, чи приходять новини загалом
        result = await conn.execute(text("""
            SELECT c.title, count(p.id) as count, max(p.created_at) as last_news
            FROM channels c
            LEFT JOIN publications p ON c.id = p.channel_id
            WHERE c.id IN (11, 13)
            GROUP BY c.title
        """))
        for row in result:
            print(f"Канал: {row.title} | Кількість новин: {row.count} | Остання: {row.last_news}")

        print("\n--- ПЕРЕВІРКА ПЕРЕКЛАДІВ/КЛАСТЕРИЗАЦІЇ ---")
        # Можливо новини є, але вони не пройшли кластеризацію?
        count_waiting = await conn.scalar(text("SELECT count(*) FROM publications WHERE story_id IS NULL"))
        print(f"Публікацій без сюжету (чекають обробки): {count_waiting}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_online_status())
