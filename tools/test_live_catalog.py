import asyncio
from database.connection import AsyncSessionLocal
from database.models import Publication, Channel, Category, ChannelCategory
from services.clustering import cluster_publication
from sqlalchemy import select
from loguru import logger
from datetime import datetime, timezone

async def test_live_catalog():
    async with AsyncSessionLocal() as session:
        # 1. Шукаємо або створюємо тестовий канал
        telegram_id = 987654321
        stmt = select(Channel).where(Channel.telegram_id == telegram_id)
        res = await session.execute(stmt)
        test_channel = res.scalar_one_or_none()
        
        if not test_channel:
            test_channel = Channel(
                telegram_id=telegram_id,
                title="Океанські глибини",
                username="deep_ocean_test",
                category="Світ"
            )
            session.add(test_channel)
            await session.flush()
        
        channel_id = test_channel.id
        
        # 2. Створюємо публікацію з темою, якої точно немає в базовому списку
        test_pub = Publication(
            channel_id=channel_id,
            telegram_message_id=1002,
            content="Біткоїн оновив історичний максимум, піднявшись вище 100 000 доларів. Експерти прогнозують подальше зростання крипторинку на тлі нових регуляторних змін у США.",
            url="https://t.me/test/1002",
            published_at=datetime.now(timezone.utc)
        )
        session.add(test_pub)
        await session.flush()
        pub_id = test_pub.id
        await session.commit()
        
        logger.info(f"Test data created: channel={channel_id}, pub={pub_id}")
    
    # 3. Запускаємо кластеризацію
    # Вона повинна:
    # - Викликати Gemini
    # - Отримати категорію (наприклад, "Космос" або "Наука")
    # - Створити категорію в БД, якщо її немає
    # - Оновити ChannelCategory
    await cluster_publication(pub_id)
    
    # 4. Перевіряємо результат
    async with AsyncSessionLocal() as session:
        # Перевіряємо чи змінилася категорія публікації
        pub = await session.get(Publication, pub_id)
        logger.info(f"Publication category: {pub.category}")
        
        # Перевіряємо ChannelCategory
        stmt = select(ChannelCategory).where(ChannelCategory.channel_id == channel_id)
        res = await session.execute(stmt)
        ch_cat = res.scalar_one_or_none()
        if ch_cat:
            cat = await session.get(Category, ch_cat.category_id)
            logger.success(f"Channel activity tracked in: {cat.emoji} {cat.name}")
            logger.success(f"Posts count: {ch_cat.posts_count}")
        else:
            logger.error("ChannelCategory was not created!")

if __name__ == "__main__":
    asyncio.run(test_live_catalog())
