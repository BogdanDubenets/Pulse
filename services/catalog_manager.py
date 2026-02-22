import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, update
from database.connection import AsyncSessionLocal
from database.models import Channel, Publication
from loguru import logger

async def recount_daily_posts():
    """
    Підраховує кількість публікацій для кожного каналу за останні 24 години
    та оновлює поле posts_count_24h в таблиці channels.
    """
    async with AsyncSessionLocal() as session:
        logger.info("Початок перерахунку активності каналів (24h)...")
        
        # Часовий проміжок для 24 годин
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Отримуємо статистику постів за 24г, групуючи за channel_id
        stmt = (
            select(Publication.channel_id, func.count(Publication.id))
            .where(Publication.published_at >= time_threshold)
            .group_by(Publication.channel_id)
        )
        
        result = await session.execute(stmt)
        stats = dict(result.all())
        
        # Отримуємо всі актині канали
        stmt_channels = select(Channel.id)
        res_channels = await session.execute(stmt_channels)
        channel_ids = res_channels.scalars().all()
        
        for ch_id in channel_ids:
            count = stats.get(ch_id, 0)
            
            # Оновлюємо значення в БД
            await session.execute(
                update(Channel)
                .where(Channel.id == ch_id)
                .values(posts_count_24h=count)
            )
            
        await session.commit()
        logger.info(f"Перерахунок завершено для {len(channel_ids)} каналів.")

async def verify_pinned_status():
    """
    (Placeholder) Перевірка закрепу для каналів партнерів.
    Буде реалізовано з використанням Client API.
    """
    logger.info("Перевірка pinned status (не реалізовано)...")
    pass
