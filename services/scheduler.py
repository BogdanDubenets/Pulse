import asyncio
from datetime import datetime
from loguru import logger
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from sqlalchemy import select, distinct
from database.connection import AsyncSessionLocal
from database.models import UserSubscription
from services.digest import get_user_digest
from database.cleanup import cleanup_old_data
from services.catalog_manager import recount_daily_posts
from config.settings import config

MORNING_HOUR = 8
EVENING_HOUR = 20
TARGET_MINUTE = 0

async def run_scheduler(bot: Bot):
    """
    Simple scheduler that checks time every 30 seconds.
    Triggers sending digests at 8:00 AM and 8:00 PM (20:00).
    """
    logger.info(f"Scheduler started. Waiting for {MORNING_HOUR}:00 and {EVENING_HOUR}:00...")
    
    # Запуск очищення при старті
    await cleanup_old_data()
    
    last_cleanup_hour = -1
    
    while True:
        now = datetime.now()
        
        # Очищення бази один раз на годину (наприклад, на 5-й хвилині)
        if now.minute == 5 and now.hour != last_cleanup_hour:
            await cleanup_old_data()
            await recount_daily_posts()
            last_cleanup_hour = now.hour
            
        # Check if it is the target time (within the minute)
        if now.minute == TARGET_MINUTE:
            if now.hour == MORNING_HOUR:
                logger.info("⏰ It's Morning Digest time! Sending...")
                await send_digests(bot, "morning")
                await asyncio.sleep(61)
            elif now.hour == EVENING_HOUR:
                logger.info("⏰ It's Evening Digest time! Sending...")
                await send_digests(bot, "evening")
                await asyncio.sleep(61)
        
        # Sleep 30 seconds to check again soon
        await asyncio.sleep(30)

async def send_digests(bot: Bot, period: str):
    """
    Надсилає дайджести всім користувачам з підписками.
    period: 'morning' або 'evening'
    """
    from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError
    
    # Отримуємо список користувачів з підписками
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(distinct(UserSubscription.user_id))
            result = await session.execute(stmt)
            user_ids = result.scalars().all()
    except Exception as e:
        logger.error(f"Помилка планувальника при отриманні користувачів: {e}")
        return

    logger.info(f"Знайдено {len(user_ids)} користувачів для {period} дайджесту.")
    
    greeting = "🌞 **Доброго ранку!**" if period == "morning" else "🌙 **Добрий вечір!**"
    sent_count = 0
    failed_count = 0
    
    for user_id in user_ids:
        try:
            # Генеруємо дайджест
            digest = await get_user_digest(user_id)
            
            if digest:
                msg_text = f"{greeting}\n\n{digest}"
                
                # Створюємо кнопку Mini App
                keyboard = None
                if config.WEBAPP_URL:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text="📱 Відкрити Pulse", 
                            web_app=WebAppInfo(url=config.WEBAPP_URL)
                        )]
                    ])
                
                try:
                    await bot.send_message(
                        user_id, 
                        msg_text, 
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=keyboard
                    )
                except TelegramRetryAfter as e:
                    # FloodWait від Bot API — чекаємо вказаний час
                    logger.warning(f"⏳ Bot API FloodWait: очікування {e.retry_after}с")
                    await asyncio.sleep(e.retry_after)
                    await bot.send_message(user_id, msg_text, parse_mode=ParseMode.MARKDOWN)
                except TelegramForbiddenError:
                    # Користувач заблокував бота
                    logger.info(f"🚫 Користувач {user_id} заблокував бота, пропускаємо.")
                    failed_count += 1
                    continue
                except Exception as parse_error:
                    # Fallback якщо Markdown не парситься
                    try:
                        await bot.send_message(
                            user_id, 
                            msg_text,
                            reply_markup=keyboard
                        )
                    except TelegramRetryAfter as e:
                        await asyncio.sleep(e.retry_after)
                        await bot.send_message(
                            user_id, 
                            msg_text,
                            reply_markup=keyboard
                        )
                    
                sent_count += 1
                logger.info(f"{period.capitalize()} дайджест надіслано {user_id}")
            else:
                logger.debug(f"Пропускаємо {user_id}: дайджест не згенеровано.")
                
            # Пауза між відправками — 1с (30 msg/s ліміт, тримаємо запас)
            await asyncio.sleep(1.0) 
            
        except Exception as e:
            failed_count += 1
            logger.error(f"Помилка відправки дайджесту {user_id}: {e}")
    
    logger.info(f"📊 {period.capitalize()} розсилка: {sent_count} надіслано, {failed_count} помилок з {len(user_ids)} користувачів")
