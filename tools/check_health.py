import asyncio
from sqlalchemy import select, func
from database.connection import AsyncSessionLocal
from database.models import Channel, UserSubscription, Publication, User
from loguru import logger
from datetime import datetime, timezone

async def check_system_health():
    async with AsyncSessionLocal() as session:
        print(f"Поточний час сервера (UTC): {datetime.now(timezone.utc)}")
        
        # 1. Стан каналів (моніторинг)
        query = select(Channel).where(Channel.is_active == True).order_by(Channel.last_scanned_at.desc())
        result = await session.execute(query)
        channels = result.scalars().all()
        
        print("\n--- СТАН МОНІТОРИНГУ КАНАЛІВ ---")
        for ch in channels:
            scanned = ch.last_scanned_at or "Ніколи"
            print(f"ID:{ch.id:2} | {ch.title[:30]:30} | Scanned: {scanned}")

        # 2. Останні підписки
        print("\n--- ОСТАННІ ПІДПИСКИ (UserSubscription) ---")
        sub_query = select(UserSubscription, Channel.title, User.username)\
            .join(Channel, UserSubscription.channel_id == Channel.id)\
            .join(User, UserSubscription.user_id == User.id)\
            .order_by(UserSubscription.created_at.desc()).limit(10)
        sub_result = await session.execute(sub_query)
        for sub, title, user in sub_result.all():
            print(f"User: @{user or 'anon'} | Channel: {title} | Created: {sub.created_at}")

        # 3. Кількість новин за сьогодні
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        news_count_query = select(func.count(Publication.id)).where(Publication.published_at >= today)
        news_count = await session.scalar(news_count_query)
        print(f"\nНовин зібрано сьогодні (з 00:00 UTC): {news_count}")

if __name__ == "__main__":
    asyncio.run(check_system_health())
