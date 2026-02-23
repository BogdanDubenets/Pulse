import asyncio
import os
import sys
from datetime import timezone

# Додаємо кореневу директорію до path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import AsyncSessionLocal
from database.models import UserSubscription
from sqlalchemy import select

async def normalize_positions():
    print("Запуск нормалізації позицій підписок...")
    async with AsyncSessionLocal() as db:
        # 1. Отримуємо всіх користувачів, які мають підписки
        stmt = select(UserSubscription.user_id).distinct()
        result = await db.execute(stmt)
        user_ids = result.scalars().all()
        
        print(f"Знайдено {len(user_ids)} користувачів з підписками.")
        
        for user_id in user_ids:
            # 2. Отримуємо всі підписки користувача, відсортовані за датою
            # Якщо позиція вже була — сортуємо за нею, якщо ні — за датою
            stmt = (
                select(UserSubscription)
                .where(UserSubscription.user_id == user_id)
                .order_by(UserSubscription.position.asc(), UserSubscription.created_at.asc())
            )
            res = await db.execute(stmt)
            subs = res.scalars().all()
            
            print(f"Користувач {user_id}: нормалізація {len(subs)} підписок...")
            
            # 3. Присвоюємо нові послідовні позиції 0, 1, 2...
            for idx, sub in enumerate(subs):
                sub.position = idx
            
        await db.commit()
    print("Нормалізацію успішно завершено.")

if __name__ == "__main__":
    asyncio.run(normalize_positions())
