import asyncio
import sys
import os
from aiogram import Bot
from sqlalchemy import select

# Додаємо кореневу директорію до path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import AsyncSessionLocal
from database.models import Channel
from config.settings import config
from loguru import logger

# Список базових каналів (username, category, title)
CORE_CHANNELS = [
    # Новини / Політика
    ("lachentyt", "📰 Події", "Лачен пише"),
    ("truexanewsua", "🏛 Політика", "Труха⚡️Україна"),
    ("uniannet", "🪖 Війна", "УНІАН"),
    ("insiderUKR", "🏛 Політика", "Украина Сейчас"),
    ("ukrpravda_news", "📰 Події", "Українська правда"),
    ("radiosvoboda", "🏛 Політика", "Радіо Свобода"),
    ("suspilnenews", "📰 Події", "Суспільне Новини"),
    ("babel", "📰 Події", "Бабель"),
    ("tsnuap", "📰 Події", "ТСН"),
    ("rbc_ukraine", "📰 Події", "РБК-Україна"),
    ("nvua_official", "🏛 Політика", "NV"),
    ("hromadske_ua", "📰 Події", "Hromadske"),
    ("bbcukrainian", "📰 Події", "BBC News Україна"),
    ("ukrinform", "📰 Події", "Укрінформ"),
    ("censor_net", "🏛 Політика", "Цензор.НЕТ"),
    ("V_Zelenskiy_official", "🏛 Політика", "Володимир Зеленський"),
    ("CinCUA", "🪖 Війна", "Головнокомандувач ЗСУ"),
    ("mvs_ukraine", "📰 Події", "МВС України"),
    ("dsns_telegram", "📰 Події", "ДСНС України"),
    ("ukrenergo", "💡 Енергетика", "Укренерго"),
    ("dtek_ua", "💡 Енергетика", "ДТЕК"),
    ("energoatom_ua", "💡 Енергетика", "Енергоатом"),
    ("epravda", "💰 Бізнес", "Економічна правда"),
    ("ainua", "💻 Технології", "AIN.UA"),
    ("doucommunity", "💻 Технології", "DOU"),
    ("itc_ua", "💻 Технології", "ITC.ua"),
    ("forbesukraine", "💰 Бізнес", "Forbes Ukraine"),
    ("liga_net", "💰 Бізнес", "LIGA.net"),
    ("devua", "💻 Технології", "dev.ua"),
    ("DeepStateUA", "🪖 Війна", "DeepState"),
    ("pravda_gerashchenko", "🪖 Війна", "Антон Геращенко"),
    ("berezoview", "🏛 Політика", "Березовий сік"),
    ("yigal_levin", "🪖 Війна", "Ігаль Левін"),
    ("truexakyiv", "📍 Київ", "Труха⚡️Київ"),
    ("h_kyiv", "📍 Київ", "Хуйовий Київ"),
    ("kievoperativ", "📍 Київ", "Київ Оперативний"),
    ("kyiv_n", "📍 Київ", "Київ Наживо"),
    ("svitlobot_a22", "📍 Київ", "СвітлоБот"),
    ("nevzorovtv", "🏛 Політика", "НЕВЗОРОВ"),
    ("dubinskypro", "🏛 Політика", "Dubinsky.pro"),
    ("mosiychuk72", "🏛 Політика", "Ігор Мосійчук"),
    ("GordonUa", "🏛 Політика", "Дмитро Гордон"),
    ("pryamiy", "🏛 Політика", "Прямий"),
    ("espresotv", "📰 Події", "Еспресо"),
    ("kanal_5", "🏛 Політика", "5 канал"),
    ("focus_ua", "📰 Події", "Фокус"),
    ("korrespondent_net", "📰 Події", "Кореспондент"),
    ("kyivindependent", "🌍 English", "The Kyiv Independent"),
    ("spravdi", "🛰 Інфофронт", "SPRAVDI"),
    ("ukraine_now", "🛰 Інфофронт", "Ukraine NOW"),
]

async def init_core_with_bot():
    bot = Bot(token=config.BOT_TOKEN.get_secret_value())
    
    async with AsyncSessionLocal() as db_session:
        logger.info(f"Розпочато резолв {len(CORE_CHANNELS)} каналів через Bot API...")
        
        added = 0
        updated = 0
        errors = 0
        
        for username, category, title in CORE_CHANNELS:
            try:
                # Перевіримо чи є вже в БД
                stmt = select(Channel).where(Channel.username == username)
                res = await db_session.execute(stmt)
                channel = res.scalar_one_or_none()
                
                if channel:
                    channel.is_core = True
                    channel.category = category
                    channel.title = title
                    updated += 1
                    logger.info(f"Оновлено: {username}")
                    continue

                # Резолвимо ID через Bot API
                chat = await bot.get_chat(f"@{username}")
                telegram_id = chat.id
                
                new_channel = Channel(
                    telegram_id=telegram_id,
                    username=username,
                    title=title,
                    category=category,
                    is_core=True,
                    is_active=True,
                    partner_status="organic"
                )
                db_session.add(new_channel)
                added += 1
                logger.info(f"Додано: {username} (ID: {telegram_id})")
                
                # Невелика пауза про всяк випадок
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Помилка для {username}: {e}")
                errors += 1
                
        await db_session.commit()
    
    await bot.session.close()
    logger.info(f"Завершено. Додано: {added}, Оновлено: {updated}, Помилок: {errors}")

if __name__ == "__main__":
    asyncio.run(init_core_with_bot())
