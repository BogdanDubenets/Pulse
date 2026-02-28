import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
from loguru import logger
from sqlalchemy import select
from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest

# Додаємо кореневу директорію до шляху імпорту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import AsyncSessionLocal
from database.models import Channel
from config.settings import config

# Список каналів для імпорту (username або link)
CHANNELS_TO_SEED = [
    # Новини та ЗМІ
    "truexanewsua", "vanek_nikolaev", "u_now", "voynareal", "novina_ua", "kievinfo_kyiv",
    # Політика
    "times_ukraina", "insiderUKR", "lachentyt", "vertikalua", "UaOnlii",
    # Блоги
    "OGoMono", "robert_magyar", "stanislav_osman", "ssternenko", "mokrivskiy",
    # Економіка
    "OstanniyCapitalist", "costukraine", "pro_podatky_fop", "ua_economy",
    # Технології
    "uamoyo", "andro_price", "webguild", "andronews_official"
]

async def seed_catalog():
    logger.info("Starting catalog seeding...")
    
    # Ініціалізація Telethon (синхронізовано з monitor.py)
    if config.TELETHON_SESSION:
        from telethon.sessions import StringSession
        session = StringSession(config.TELETHON_SESSION)
        logger.info("Using StringSession")
    else:
        session = 'session/pulse_monitor'
        logger.info(f"Using SQLiteSession at {session}")

    client = TelegramClient(
        session,
        config.API_ID,
        config.API_HASH
    )
    
    try:
        await client.start(phone=config.PHONE_NUMBER)
        logger.info("Telethon connected and authorized.")
    except Exception as e:
        logger.error(f"Failed to start Telethon: {e}")
        return

    async with AsyncSessionLocal() as session_db:
        for username in CHANNELS_TO_SEED:
            try:
                # 1. Перевірка на дублікат у БД
                stmt = select(Channel).where(Channel.username == username)
                res = await session_db.execute(stmt)
                if res.scalar_one_or_none():
                    logger.info(f"Channel @{username} already exists in DB, skipping.")
                    continue

                # 2. Перевірка "живості" через Telegram API
                logger.info(f"Checking @{username} liveness...")
                try:
                    entity = await client.get_entity(username)
                    
                    # Отримуємо останнє повідомлення для перевірки активності
                    messages = await client.get_messages(entity, limit=1)
                    if not messages:
                        logger.warning(f"Channel @{username} has no posts. Skipping.")
                        continue
                    
                    last_post_date = messages[0].date
                    # Якщо останній пост старіший за 30 днів - канал "мертвий"
                    if datetime.now(timezone.utc) - last_post_date > timedelta(days=30):
                        logger.warning(f"Channel @{username} is inactive (last post {last_post_date}). Skipping.")
                        continue

                    # 3. Додавання в базу
                    new_channel = Channel(
                        telegram_id=entity.id,
                        username=username,
                        title=entity.title,
                        is_active=True,
                        is_core=True, # Позначаємо як базові канали
                        last_scanned_at=None # Тригеримо негайне сканування монітором
                    )
                    session_db.add(new_channel)
                    logger.success(f"Added new channel: {entity.title} (@{username})")
                    
                except Exception as e:
                    logger.error(f"Failed to fetch @{username} from Telegram: {e}")
                    continue

            except Exception as e:
                logger.error(f"Error processing @{username}: {e}")

        await session_db.commit()
    
    await client.disconnect()
    logger.success("Catalog seeding completed!")

if __name__ == "__main__":
    asyncio.run(seed_catalog())
