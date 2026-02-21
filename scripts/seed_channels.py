import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import Channel
from sqlalchemy import select
from loguru import logger
from services.channel_service import channel_service

# Початковий список каналів з техзавдання (без хардкод-ідентіфікаторів!)
INITIAL_CHANNELS = [
    {"title": "Українська правда", "username": "pravdaGerashchenko", "category": "Новини"},
    {"title": "НВ", "username": "nvua_official", "category": "Новини"},
    {"title": "Forbes Ukraine", "username": "forbes_ukraine", "category": "Бізнес"},
    {"title": "Економічна правда", "username": "epravda", "category": "Бізнес"},
    {"title": "DOU", "username": "doucommunity", "category": "Технології"},
]

async def seed_channels():
    """Наповнення бази з автоматичною валідацією ID через Telegram API"""
    logger.info(f"Starting seed for {len(INITIAL_CHANNELS)} channels...")
    
    for ch_data in INITIAL_CHANNELS:
        logger.info(f"Seeding/Validating channel: {ch_data['title']} (@{ch_data['username']})")
        
        # Використовуємо наш новий сервіс для безпечного додавання
        channel, error = await channel_service.get_or_create_channel(ch_data['username'])
        
        if channel:
            # Оновлюємо категорію (якщо вона відрізняється від дефолтної)
            await channel_service.update_category(channel.id, ch_data['category'])
            logger.info(f"✅ Channel '{ch_data['title']}' is ready with TG ID: {channel.telegram_id}")
        else:
            logger.error(f"❌ Failed to seed {ch_data['title']}: {error}")
    
    logger.info("Seeding completed!")

if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.getcwd())
    asyncio.run(seed_channels())
