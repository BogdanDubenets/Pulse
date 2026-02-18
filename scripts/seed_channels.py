import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import Channel
from sqlalchemy import select
from loguru import logger

# Початковий список каналів з техзавдання
INITIAL_CHANNELS = [
    {"title": "Українська правда", "username": "pravdaGerashchenko", "telegram_id": -1001055530773, "category": "Новини"}, # приклади ID
    {"title": "НВ", "username": "nvua_official", "telegram_id": -1001146313181, "category": "Новини"},
    {"title": "Forbes Ukraine", "username": "forbesukraine", "telegram_id": -1001490215707, "category": "Бізнес"},
    {"title": "Економічна правда", "username": "epravda", "telegram_id": -1001140027209, "category": "Бізнес"},
    {"title": "DOU", "username": "doucommunity", "telegram_id": -1001111624891, "category": "Технології"},
]

async def seed_channels():
    async with AsyncSessionLocal() as session:
        for ch_data in INITIAL_CHANNELS:
            # Перевіряємо чи вже є такий канал
            result = await session.execute(select(Channel).where(Channel.username == ch_data["username"]))
            existing = result.scalar_one_or_none()
            
            if not existing:
                new_channel = Channel(
                    title=ch_data["title"],
                    username=ch_data["username"],
                    telegram_id=ch_data["telegram_id"],
                    category=ch_data["category"],
                    is_active=True
                )
                session.add(new_channel)
                logger.info(f"Added channel to seed: {ch_data['title']}")
            else:
                logger.debug(f"Channel {ch_data['title']} already exists")
        
        await session.commit()
        logger.info("Seeding completed!")

if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.getcwd())
    asyncio.run(seed_channels())
