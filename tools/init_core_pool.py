import asyncio
import sys
import os

# Додаємо кореневу директорію до path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, update
from database.connection import AsyncSessionLocal
from database.models import Channel
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
    
    # Офіційні / Держструктури
    ("V_Zelenskiy_official", "🏛 Політика", "Володимир Зеленський"),
    ("CinCUA", "🪖 Війна", "Головнокомандувач ЗСУ"),
    ("mvs_ukraine", "📰 Події", "МВС України"),
    ("dsns_telegram", "📰 Події", "ДСНС України"),
    ("ukrenergo", "💡 Енергетика", "Укренерго"),
    ("dtek_ua", "💡 Енергетика", "ДТЕК"),
    ("energoatom_ua", "💡 Енергетика", "Енергоатом"),
    
    # Бізнес / Технології
    ("epravda", "💰 Бізнес", "Економічна правда"),
    ("ainua", "💻 Технології", "AIN.UA"),
    ("doucommunity", "💻 Технології", "DOU"),
    ("itc_ua", "💻 Технології", "ITC.ua"),
    ("forbesukraine", "💰 Бізнес", "Forbes Ukraine"),
    ("liga_net", "💰 Бізнес", "LIGA.net"),
    ("devua", "💻 Технології", "dev.ua"),
    
    # Війна / Аналітика
    ("DeepStateUA", "🪖 Війна", "DeepState"),
    ("pravda_gerashchenko", "🪖 Війна", "Антон Геращенко"),
    ("berezoview", "🏛 Політика", "Березовий сік"),
    ("yigal_levin", "🪖 Війна", "Ігаль Левін"),
    
    # Регіональні (Київ)
    ("truexakyiv", "📍 Київ", "Труха⚡️Київ"),
    ("h_kyiv", "📍 Київ", "Хуйовий Київ"),
    ("kievoperativ", "📍 Київ", "Київ Оперативний"),
    ("kyiv_n", "📍 Київ", "Київ Наживо"),
    ("svitlobot_a22", "📍 Київ", "СвітлоБот"),
    
    # Інші / Медіа
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

async def init_core():
    async with AsyncSessionLocal() as session:
        logger.info(f"Початок ініціалізації {len(CORE_CHANNELS)} базових каналів...")
        
        # Спочатку скидаємо is_core для всіх (якщо треба)
        # await session.execute(update(Channel).values(is_core=False))
        
        added_count = 0
        updated_count = 0
        
        for username, category, title in CORE_CHANNELS:
            # Шукаємо за юзернеймом
            stmt = select(Channel).where(Channel.username == username)
            result = await session.execute(stmt)
            channel = result.scalar_one_or_none()
            
            if channel:
                channel.is_core = True
                channel.category = category
                channel.title = title
                updated_count += 1
            else:
                new_channel = Channel(
                    username=username,
                    title=title,
                    category=category,
                    is_core=True,
                    is_active=True,
                    partner_status="organic"
                )
                session.add(new_channel)
                added_count += 1
                
        await session.commit()
        logger.info(f"Завершено! Додано: {added_count}, Оновлено: {updated_count}")

if __name__ == "__main__":
    asyncio.run(init_core())
