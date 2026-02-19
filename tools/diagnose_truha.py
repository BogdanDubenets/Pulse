import asyncio
from sqlalchemy import select
from database.connection import AsyncSessionLocal
from database.models import Channel, UserSubscription, Publication
from loguru import logger

async def diagnose_truha():
    async with AsyncSessionLocal() as session:
        # 1. Знайти канал Труха
        query = select(Channel).where(Channel.title.ilike('%Труха%'))
        result = await session.execute(query)
        channels = result.scalars().all()
        
        if not channels:
            print("❌ Канал 'Труха' не знайдено в базі!")
            return
            
        for ch in channels:
            print(f"--- Канал: {ch.title} (ID: {ch.id}, TG_ID: {ch.telegram_id}, Active: {ch.is_active}) ---")
            
            # 2. Перевірити підписки
            sub_query = select(UserSubscription).where(UserSubscription.channel_id == ch.id)
            sub_result = await session.execute(sub_query)
            subs = sub_result.scalars().all()
            print(f"Кількість підписників у базі: {len(subs)}")
            
            # 3. Перевірити останні новини саме цього каналу
            pub_query = select(Publication).where(Publication.channel_id == ch.id).order_by(Publication.published_at.desc()).limit(5)
            pub_result = await session.execute(pub_query)
            pubs = pub_result.scalars().all()
            
            if not pubs:
                print("❌ Новин від цього каналу в базі немає.")
            else:
                print(f"✅ Остання новина в базі: {pubs[0].published_at}")
                for p in pubs:
                    print(f"  - [{p.published_at}] {p.content[:50]}...")

        # 4. Загальна перевірка — чи приходять хоч якісь новини зараз?
        print("\n--- Останні новини в системі (будь-які) ---")
        any_pub_query = select(Publication).order_by(Publication.published_at.desc()).limit(5)
        any_pub_result = await session.execute(any_pub_query)
        any_pubs = any_pub_result.scalars().all()
        for p in any_pubs:
            print(f"  - [{p.published_at}] ID:{p.channel_id} | {p.content[:50]}...")

if __name__ == "__main__":
    asyncio.run(diagnose_truha())
