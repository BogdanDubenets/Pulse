"""
Утиліти для автоочищення чату — видалення сервісних повідомлень через N секунд.
"""

import asyncio
from aiogram.types import Message
from loguru import logger


async def auto_delete(message: Message, delay: int = 5):
    """Видалити повідомлення через delay секунд"""
    try:
        await asyncio.sleep(delay)
        await message.delete()
    except Exception as e:
        # Повідомлення вже видалено або немає прав
        logger.debug(f"Cannot delete message: {e}")


def schedule_delete(message: Message, delay: int = 5):
    """Запланувати видалення (не блокує виконання)"""
    asyncio.create_task(auto_delete(message, delay))
