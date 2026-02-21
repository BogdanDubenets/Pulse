import asyncio
from typing import Optional, Tuple
from telethon.tl.types import Channel as TelethonChannel
from loguru import logger
from database.models import Channel
from database.connection import AsyncSessionLocal
from sqlalchemy import select
from services.monitor import monitor

class ChannelService:
    """Сервіс для валідації та створення каналів через Telegram API"""

    @staticmethod
    async def get_or_create_channel(identifier: str) -> Tuple[Optional[Channel], Optional[str]]:
        """
        Знаходить канал у базі або створює новий після валідації через Telethon.
        identifier: username (з @ або без) або посилання t.me/...
        Returns: (Channel object, error_message)
        """
        # Очищення ідентифікатора
        clean_id = identifier.strip().replace('@', '').split('/')[-1]
        
        # Перевіряємо, чи це числовий ID (може бути з мінусом)
        is_numeric = False
        try:
            int_id = int(clean_id)
            is_numeric = True
        except ValueError:
            int_id = None

        async with AsyncSessionLocal() as session:
            # 1. Шукаємо в базі
            if is_numeric:
                # Якщо це ID, шукаємо за telegram_id
                # Telethon ID зазвичай позитивні, а в Bot API - з -100. Приводимо до формату Telethon.
                search_id = int_id
                if str(search_id).startswith("-100"):
                    search_id = int(str(search_id)[4:])
                elif str(search_id).startswith("-"):
                    search_id = int(str(search_id)[1:])
                
                result = await session.execute(
                    select(Channel).where(Channel.telegram_id == search_id)
                )
            else:
                # Якщо це username, шукаємо за username
                result = await session.execute(
                    select(Channel).where(Channel.username.ilike(clean_id))
                )
            
            channel = result.scalar_one_or_none()
            if channel:
                return channel, None

            # 2. Якщо в базі немає — резолвимо через Telegram
            try:
                if not monitor.client.is_connected():
                    await monitor.start()
                
                # Для get_entity краще передавати int якщо це число
                to_resolve = int_id if is_numeric else clean_id
                entity = await monitor.client.get_entity(to_resolve)
                
                if not isinstance(entity, TelethonChannel):
                    return None, f"'{identifier}' не є каналом (можливо це група або користувач)"

                # 3. Перевіряємо ще раз за отриманим telegram_id (можливо в базі він під іншим ніком)
                result = await session.execute(
                    select(Channel).where(Channel.telegram_id == entity.id)
                )
                channel = result.scalar_one_or_none()
                if channel:
                    # Оновлюємо username якщо він змінився
                    if channel.username != username:
                        channel.username = username
                        await session.commit()
                    return channel, None

                # 4. Створюємо новий канал з ГАРАНТОВАНО правильними даними
                new_channel = Channel(
                    telegram_id=entity.id,
                    username=getattr(entity, 'username', None) or clean_id if not is_numeric else getattr(entity, 'username', None),
                    title=entity.title,
                    category="📰 Події", # Тимчасова
                    is_active=True
                )
                session.add(new_channel)
                await session.commit()
                await session.refresh(new_channel)
                
                logger.info(f"Validated and created new channel: {entity.title} (TG ID: {entity.id})")
                
                # Реєструємо в моніторингу
                await monitor.track_channel(new_channel.id)
                
                return new_channel, None

            except Exception as e:
                logger.error(f"Failed to validate channel '{identifier}': {e}")
                return None, f"Не вдалося знайти канал '{identifier}' у Telegram. Перевірте правильність посилання."

    @staticmethod
    async def update_category(channel_id: int, category: str):
        """Оновлення категорії каналу"""
        async with AsyncSessionLocal() as session:
            channel = await session.get(Channel, channel_id)
            if channel:
                channel.category = category
                await session.commit()
                logger.info(f"Updated category for '{channel.title}' to '{category}'")

channel_service = ChannelService()
