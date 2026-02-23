import asyncio
import os
import sys

# Додаємо кореневу директорію до path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import AsyncSessionLocal
from sqlalchemy import text

async def add_position_column():
    print("Додавання колонки 'position' до 'user_subscriptions'...")
    async with AsyncSessionLocal() as session:
        try:
            # Перевіряємо чи колонка вже існує (для ідемпотентності)
            check_stmt = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='user_subscriptions' AND column_name='position';
            """)
            result = await session.execute(check_stmt)
            if result.fetchone():
                print("Колонка 'position' вже існує.")
                return

            # Додаємо колонку
            alter_stmt = text("ALTER TABLE user_subscriptions ADD COLUMN position INTEGER DEFAULT 0;")
            await session.execute(alter_stmt)
            
            # Ініціалізуємо позиції існуючими ID або за дефолтом
            update_stmt = text("UPDATE user_subscriptions SET position = id WHERE position = 0;")
            await session.execute(update_stmt)
            
            await session.commit()
            print("Колонку 'position' успішно додано.")
        except Exception as e:
            print(f"Помилка при додаванні колонки: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(add_position_column())
