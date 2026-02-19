from telethon import TelegramClient, events
from telethon.tl.types import Channel as TelethonChannel
from telethon.errors import FloodWaitError
from loguru import logger
from config.settings import config
from database.connection import AsyncSessionLocal
from database.models import Channel, Publication
from sqlalchemy import select
import asyncio
from datetime import datetime

import os

from telethon.sessions import StringSession

class ChannelMonitor:
    def __init__(self):
        # Використовуємо StringSession для хмари (якщо є) або локальний файл
        if config.TELETHON_SESSION:
            session = StringSession(config.TELETHON_SESSION)
            logger.info("Using StringSession for Telethon")
        else:
            # Переконуємось, що папка для сесії існує (для локальної розробки)
            session_path = 'session/pulse_monitor'
            os.makedirs(os.path.dirname(session_path), exist_ok=True)
            session = session_path
            logger.info(f"Using SQLiteSession at {session_path}")
        
        self.client = TelegramClient(
            session, 
            config.API_ID, 
            config.API_HASH.strip()
        )
        # Cache: telegram_id -> database_id
        self.active_channels: dict[int, int] = {}
        self.username_to_id: dict[str, int] = {}
        # Cache: telegram chat_id -> chat title (для логів, без зайвих API-запитів)
        self.chat_title_cache: dict[int, str] = {}
        # Cache: telegram chat_id -> username (для URL)
        self.chat_username_cache: dict[int, str] = {}
        # Лічильник FloodWait інцидентів
        self.flood_wait_count: int = 0
        self.last_flood_wait: datetime | None = None

    async def start(self):
        logger.info("Starting Telethon Client (Event-Driven)...")
        try:
            await self.client.start(phone=config.PHONE_NUMBER)
        except FloodWaitError as e:
            logger.warning(f"⏳ FloodWait при старті Telethon: очікування {e.seconds}с...")
            self.flood_wait_count += 1
            self.last_flood_wait = datetime.now()
            await asyncio.sleep(e.seconds)
            await self.client.start(phone=config.PHONE_NUMBER)
        
        # Initial fetch
        await self.refresh_channels()
        
        # Register Handler
        self.client.add_event_handler(self.handle_new_message, events.NewMessage(incoming=True))
        logger.info("Telethon Client started & Event Handler registered!")

    async def refresh_channels(self):
        """Оновлює локальний кеш активних каналів з БД."""
        try:
            from database.models import UserSubscription
            async with AsyncSessionLocal() as session:
                # Вибираємо лише ті канали, у яких є підписники
                query = (
                    select(Channel)
                    .join(UserSubscription, Channel.id == UserSubscription.channel_id)
                    .where(Channel.is_active == True)
                    .distinct()
                )
                result = await session.execute(query)
                channels = result.scalars().all()
                
            self.active_channels.clear()
            self.username_to_id.clear()
            
            for ch in channels:
                if ch.telegram_id:
                    self.active_channels[ch.telegram_id] = ch.id
                    # Telethon часто використовує -100... для каналів
                    if ch.telegram_id > 0:
                         self.active_channels[int(f"-100{ch.telegram_id}")] = ch.id
                
                if ch.username:
                    clean_username = ch.username.lower().replace('@', '')
                    self.username_to_id[clean_username] = ch.id
                    # Попередньо кешуємо username для побудови URL
                    if ch.telegram_id:
                        self.chat_username_cache[ch.telegram_id] = clean_username
                        self.chat_username_cache[int(f"-100{ch.telegram_id}")] = clean_username
                    
            logger.info(f"Оновлено список каналів: {len(channels)} каналів (flood_wait: {self.flood_wait_count})")
        except Exception as e:
            logger.error(f"Помилка оновлення каналів: {e}")

    async def is_ad(self, text: str, channel_id: int = None) -> bool:
        """
        Перевіряє, чи є повідомлення рекламою, враховуючи контекст каналу.
        """
        if not text:
            return False
            
        ad_markers = [
            "#реклама", "#promo", "реклама", "за посиланням", 
            "купити", "знижка", "підписуйтесь", "реєструйтеся",
            "зареєструватися", "гроші", "казино", "ставки",
            "промокод", "заробіток", "виплати", "крипта",
            "біткоїн", "bitcoin", "курс валют тут", "дивіться за посиланням",
            "переходьте", "підпишись", "еко-система", "інвестування",
            "безкоштовно", "дарма", "акція", "розіграш", "айфон",
            "інтим", "бутик", "шоп", "18+", "🔞", "замовити",
            "магазин", "знижк", "промокод", "ловіть", "тільки сьогодні",
            "t.me/+", "t.me/joinchat"
        ]

        # Контекстні винятки
        context_exceptions = []
        if channel_id:
            try:
                async with AsyncSessionLocal() as session:
                    channel = await session.get(Channel, channel_id)
                    if channel and channel.category:
                        cat = channel.category.lower()
                        if "крипт" in cat or "фінанс" in cat:
                            context_exceptions.extend(["крипта", "біткоїн", "bitcoin", "інвестування", "виплати"])
                        if "подорож" in cat or "туризм" in cat:
                            context_exceptions.extend(["за посиланням", "дивіться за посиланням", "переходьте"])
            except Exception as e:
                logger.warning(f"Помилка перевірки контексту реклами: {e}")
        
        text_lower = text.lower()
        for marker in ad_markers:
            if marker in text_lower:
                # Перевірка на винятки
                if any(exc in marker for exc in context_exceptions):
                    continue
                return True
        return False

    async def _get_chat_info(self, event) -> tuple[int | None, str | None, str | None]:
        """
        Отримує інформацію про чат з кешу або API (з обробкою FloodWait).
        Повертає: (db_channel_id, chat_title, chat_username)
        """
        chat_id = event.chat_id
        
        # 1. Спершу шукаємо в кеші за ID
        db_channel_id = self.active_channels.get(chat_id)
        
        if db_channel_id:
            # Є в кеші — повертаємо без API-запиту
            title = self.chat_title_cache.get(chat_id)
            username = self.chat_username_cache.get(chat_id)
            
            # Якщо title ще немає в кеші — запитуємо один раз і кешуємо
            if title is None:
                try:
                    chat = await event.get_chat()
                    title = getattr(chat, 'title', 'Unknown')
                    username = getattr(chat, 'username', None)
                    self.chat_title_cache[chat_id] = title
                    if username:
                        self.chat_username_cache[chat_id] = username.lower()
                except FloodWaitError as e:
                    logger.warning(f"⏳ FloodWait при get_chat: {e.seconds}с")
                    self.flood_wait_count += 1
                    self.last_flood_wait = datetime.now()
                    await asyncio.sleep(e.seconds)
                    # Повторна спроба
                    chat = await event.get_chat()
                    title = getattr(chat, 'title', 'Unknown')
                    username = getattr(chat, 'username', None)
                    self.chat_title_cache[chat_id] = title
                    if username:
                        self.chat_username_cache[chat_id] = username.lower()
                        
            return db_channel_id, title, username
        
        # 2. Fallback: якщо немає по ID — спробуємо через username
        # Для цього потрібен get_chat() — але тільки 1 раз
        if chat_id not in self.chat_title_cache:
            try:
                chat = await event.get_chat()
                title = getattr(chat, 'title', 'Unknown')
                username = getattr(chat, 'username', None)
                self.chat_title_cache[chat_id] = title
                if username:
                    self.chat_username_cache[chat_id] = username.lower()
                    db_channel_id = self.username_to_id.get(username.lower())
                    if db_channel_id:
                        return db_channel_id, title, username
            except FloodWaitError as e:
                logger.warning(f"⏳ FloodWait при fallback get_chat: {e.seconds}с")
                self.flood_wait_count += 1
                self.last_flood_wait = datetime.now()
                await asyncio.sleep(e.seconds)
                return None, None, None
            except Exception:
                pass

        return None, None, None

    async def handle_new_message(self, event):
        """Обробник нових повідомлень з обробкою FloodWait."""
        try:
            # Тільки канали
            if not event.is_channel:
                return

            # Отримуємо інфо з кешу (мінімум API-запитів)
            db_channel_id, chat_title, chat_username = await self._get_chat_info(event)
            
            if not db_channel_id:
                return

            text = event.message.message
            if await self.is_ad(text, channel_id=db_channel_id):
                logger.info(f"🚫 Реклама (context-aware), пропускаємо: {chat_title}")
                return

            logger.info(f"📩 Нове повідомлення: {chat_title} ({event.chat_id})")
            
            # Обробка
            await self.save_and_cluster(event, db_channel_id, chat_username)
            
        except FloodWaitError as e:
            logger.warning(f"⏳ FloodWait у handle_new_message: {e.seconds}с")
            self.flood_wait_count += 1
            self.last_flood_wait = datetime.now()
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"Помилка обробки повідомлення: {e}")

    async def save_and_cluster(self, event, channel_id, chat_username=None):
        try:
            text = event.message.message
            if not text: return
            
            msg_id = event.message.id
            date = event.message.date
            views = getattr(event.message, 'views', 0) or 0
            
            # URL — використовуємо кешований username
            username = chat_username or self.chat_username_cache.get(event.chat_id)
            url = f"https://t.me/{username}/{msg_id}" if username else None

            async with AsyncSessionLocal() as session:
                # Дедуплікація
                exists = await session.scalar(
                    select(Publication).where(
                        Publication.channel_id == channel_id, 
                        Publication.telegram_message_id == msg_id
                    )
                )
                if exists: return

                new_pub = Publication(
                    channel_id=channel_id,
                    telegram_message_id=msg_id,
                    content=text,
                    url=url,
                    published_at=date,
                    views=views
                )
                session.add(new_pub)
                await session.commit()
                await session.refresh(new_pub)
                pub_id = new_pub.id
            
            # Trigger Clustering (Async)
            from services.clustering import cluster_publication
            asyncio.create_task(cluster_publication(pub_id))
            
        except FloodWaitError as e:
            logger.warning(f"⏳ FloodWait у save_and_cluster: {e.seconds}с")
            self.flood_wait_count += 1
            self.last_flood_wait = datetime.now()
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"Помилка збереження/кластеризації: {e}")

    async def stop(self):
        """Відключає клієнт."""
        if self.client.is_connected():
            await self.client.disconnect()
            logger.info(f"Telethon відключено (FloodWait інцидентів за сесію: {self.flood_wait_count})")

    async def run_monitoring(self):
        """Підтримує клієнт активним та оновлює список каналів."""
        try:
            await self.start()
        except FloodWaitError as e:
            logger.error(f"⏳ FloodWait при запуску: очікування {e.seconds}с...")
            self.flood_wait_count += 1
            self.last_flood_wait = datetime.now()
            await asyncio.sleep(e.seconds)
            await self.start()
        except Exception as e:
            logger.error(f"Не вдалося запустити Telethon: {e}")
            return

        logger.info("Моніторинг (Event-Driven) запущено.")
        try:
            while True:
                await asyncio.sleep(300)  # Оновлення списку каналів кожні 5 хв
                try:
                    await self.refresh_channels()
                except FloodWaitError as e:
                    logger.warning(f"⏳ FloodWait при refresh: {e.seconds}с")
                    self.flood_wait_count += 1
                    self.last_flood_wait = datetime.now()
                    await asyncio.sleep(e.seconds)
        except asyncio.CancelledError:
            logger.info("Моніторинг зупинено.")
            await self.stop()
            raise

monitor = ChannelMonitor()
