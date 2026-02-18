import asyncio
from sqlalchemy import text
from database.connection import AsyncSessionLocal

async def check_db_size():
    async with AsyncSessionLocal() as session:
        # Total DB size
        db_size_query = text("SELECT pg_size_pretty(pg_database_size(current_database()))")
        db_size_res = await session.execute(db_size_query)
        total_size = db_size_res.scalar()

        # Table-wise size
        table_size_query = text("""
            SELECT 
                relname AS table_name, 
                pg_size_pretty(pg_total_relation_size(relid)) AS total_size
            FROM pg_catalog.pg_statio_user_tables 
            ORDER BY pg_total_relation_size(relid) DESC;
        """)
        table_res = await session.execute(table_size_query)
        tables = table_res.all()

        print(f"📁 **Загальний об'єм БД**: {total_size}")
        print("-" * 30)
        print("📊 **Розмір таблиць (включаючи індекси):**")
        for table, size in tables:
            print(f"- {table}: {size}")

if __name__ == "__main__":
    asyncio.run(check_db_size())
