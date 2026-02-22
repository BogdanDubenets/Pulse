import asyncio
import sys
import os

# Додаємо кореневу директорію до path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func
from database.connection import AsyncSessionLocal
from database.models import Channel, Publication
from loguru import logger

async def inspect():
    async with AsyncSessionLocal() as session:
        # Рахуємо всього каналів
        count_stmt = select(func.count()).select_from(Channel)
        count = await session.scalar(count_stmt)
        logger.info(f"Всього каналів у БД: {count}")

        # Рахуємо канали з категоріями
        cat_stmt = select(Channel.category, func.count()).group_by(Channel.category).order_by(func.count().desc())
        categories = await session.execute(cat_stmt)
        logger.info("Категорії та кількість каналів у них:")
        for cat, num in categories:
            logger.info(f"- {cat}: {num}")

        # Беремо останні 10 каналів для прикладу
        recent_stmt = select(Channel).order_by(Channel.created_at.desc()).limit(10)
        recent = await session.execute(recent_stmt)
        logger.info("Останні додані канали:")
        for row in recent.scalars():
            logger.info(f"ID: {row.id}, Title: {row.title}, Username: {row.username}, Category: {row.category}")

if __name__ == "__main__":
    asyncio.run(inspect())
