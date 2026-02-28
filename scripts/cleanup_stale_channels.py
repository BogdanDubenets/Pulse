import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from loguru import logger

# Додаємо кореневу директорію проекту в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import AsyncSessionLocal
from database.models import Channel, UserSubscription
from services.monitor import monitor
from sqlalchemy import select

async def cleanup_stale_channels():
    """
    Проходить по всіх активних каналах у базі та деактивує ті,
    що не публікували нічого понад 30 днів.
    """
    logger.info("🚀 Запуск глобальної чистки неактивних каналів...")
    
    try:
        # Стартуємо клієнт Telethon
        if not monitor.client.is_connected():
            await monitor.client.start()
            
        async with AsyncSessionLocal() as session:
            # Вибираємо всі активні канали (крім core)
            stmt = select(Channel).where(Channel.is_active == True, Channel.is_core == False)
            res = await session.execute(stmt)
            channels = res.scalars().all()
            
            logger.info(f"На аналізі: {len(channels)} каналів.")
            
            deactivated_count = 0
            for ch in channels:
                identifier = ch.username or ch.telegram_id
                if not identifier:
                    continue
                
                # Перевірка liveness ( Userbot iter_messages )
                is_live = await monitor.check_channel_liveness(identifier)
                
                if not is_live:
                    logger.warning(f"❄️ Канал '{ch.title}' (@{ch.username}) неактивний > 30 днів. Деактивуємо.")
                    ch.is_active = False
                    deactivated_count += 1
                
                # Невелика затримка щоб не ловити FloodWait
                await asyncio.sleep(1)
            
            if deactivated_count > 0:
                await session.commit()
                logger.info(f"✅ Успішно деактивовано {deactivated_count} каналів.")
            else:
                logger.info("✅ Всі канали активні. Деактивація не потрібна.")
                
    except Exception as e:
        logger.error(f"Помилка під час чистки: {e}")
    finally:
        await monitor.stop()

if __name__ == "__main__":
    asyncio.run(cleanup_stale_channels())
