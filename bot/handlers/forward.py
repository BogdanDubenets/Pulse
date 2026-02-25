import re
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.connection import AsyncSessionLocal
from database.models import Channel, UserSubscription
from sqlalchemy import select, func
from loguru import logger
from bot.utils import schedule_delete
from database.users import upsert_user

from bot.categories import THEMATIC_CATEGORIES, REGIONAL_CATEGORIES, AUTHOR_CATEGORIES
from services.ai_service import classify_channel
from services.monitor import monitor
from services.channel_service import channel_service
from services.subscription_service import subscription_service

router = Router()

# Патерн для розпізнавання каналів у тексті
CHANNEL_PATTERN = re.compile(
    r'(?:https?://)?(?:t\.me|telegram\.me)/([a-zA-Z_][a-zA-Z0-9_]{3,})'  # t.me/username
    r'|@([a-zA-Z_][a-zA-Z0-9_]{3,})',  # @username
    re.IGNORECASE
)


@router.message(F.forward_from_chat)
async def handle_forward(message: Message):
    """Обробка пересланого повідомлення з каналу"""
    try:
        chat = message.forward_from_chat
        if chat.type != "channel":
            err = await message.reply(
                "🏗️ <b>Працюємо — скоро з'явиться!</b>\n\n"
                "Наразі я обробляю лише Telegram-канали. Переходьте в Pulse, щоб побачити всі можливості. ✨",
                reply_markup=get_webapp_kb()
            )
            schedule_delete(message, 5)
            schedule_delete(err, 10)
            return

        logger.info(f"Forward from channel: {chat.title} (id={chat.id}) by user {message.from_user.id}")

        # Реєстрація користувача (про всяк випадок, якщо пропустив /start)
        await upsert_user(
            user_id=message.from_user.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username,
            language_code=message.from_user.language_code
        )

        async with AsyncSessionLocal() as session:
            # Використовуємо сервіс для валідації та отримання/створення каналу
            # Пріоритет юзернейму, бо він надійніший для резолвінгу
            identifier = f"@{chat.username}" if chat.username else str(chat.id)
            channel, error = await channel_service.get_or_create_channel(identifier)
            
            if error or not channel:
                await message.reply(f"❌ Помилка: {error}")
                return

            # Перевіряємо підписку
            sub_result = await session.execute(
                select(UserSubscription).where(
                    UserSubscription.user_id == message.from_user.id,
                    UserSubscription.channel_id == channel.id
                )
            )
            subscription = sub_result.scalar_one_or_none()
            
            if not subscription:
                # ПЕРЕВІРКА ЛІМІТУ
                status_info = await subscription_service.get_user_status(message.from_user.id, session)
                if not status_info["can_add"]:
                    await message.answer(
                        f"🚫 <b>Ліміт вичерпано</b>\n\n"
                        f"На плані <b>{status_info['tier'].capitalize()}</b> ви можете відстежувати до {status_info['limit']} каналів.\n\n"
                        f"Будь ласка, перейдіть у Mini App, щоб видалити зайві канали або покращити свій план! ✨",
                        reply_markup=get_webapp_kb()
                    )
                    return

                # Визначаємо наступну позицію (черга додавання)
                pos_stmt = select(func.max(UserSubscription.position)).where(UserSubscription.user_id == message.from_user.id)
                pos_res = await session.execute(pos_stmt)
                max_pos = pos_res.scalar()
                next_pos = (max_pos + 1) if max_pos is not None else 0

                session.add(UserSubscription(
                    user_id=message.from_user.id,
                    channel_id=channel.id,
                    position=next_pos
                ))
                await session.commit()
                status = "\n\n✅ Підписано! Тепер я стежу за цим каналом."
                # Запускаємо миттєвий збір новин через монітор
                asyncio.create_task(monitor.track_channel(channel.id))
            else:
                status = "\n\n✅ Ви вже підписані на цей канал."
            
            # Якщо канал зовсім новий (щойно створений сервісом), запускаємо аналіз категорії
            
            bot_msg = await message.answer(
                f"📺 <b>{channel.title}</b>"
                f"{status}",
                reply_markup=get_webapp_kb()
            )

            # AI класифікація (якщо категорія ще дефолтна)
            if channel.category == "📰 Події":
                sample_text = message.text or message.caption or ""
                ai_category = await classify_channel(
                    title=channel.title,
                    username=channel.username,
                    sample_text=sample_text
                )
                await channel_service.update_category(channel.id, ai_category)
                await bot_msg.edit_text(
                    f"📺 <b>{channel.title}</b>\n"
                    f"📂 Категорія: <b>{ai_category}</b>"
                    f"{status}"
                )

            schedule_delete(message, 3)
            schedule_delete(bot_msg, 10)
        
    except Exception as e:
        logger.exception(f"ERROR in handle_forward: {e}")
        await message.reply(f"Сталася помилка: {e}")


# ── Обробка посилань та @юзернеймів ───────────────────────────

@router.message(F.text)
async def handle_channel_link(message: Message):
    """Обробка текстових повідомлень з t.me/link або @username (в будь-якій позиції)"""
    text = message.text.strip()
    match = CHANNEL_PATTERN.search(text)
    
    if not match:
        # Текст без каналу або інший запит — ведемо в Mini App
        hint = await message.answer(
            "🏗️ <b>Працюємо — скоро з'явиться!</b>\n\n"
            "Переходьте в Pulse, щоб користуватися всіма функціями. 📱✨",
            reply_markup=get_webapp_kb()
        )
        schedule_delete(message, 5)
        schedule_delete(hint, 10)
        return
    
    # Витягуємо юзернейм з посилання або @mention
    username = match.group(1) or match.group(2)
    logger.info(f"Channel link detected: @{username} from user {message.from_user.id}")
    
    # Реєстрація користувача
    await upsert_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
        language_code=message.from_user.language_code
    )
    
    try:
        # Використовуємо сервіс для валідації та отримання/створення каналу
        channel, error = await channel_service.get_or_create_channel(username)
        
        if error or not channel:
            bot_msg = await message.answer(f"❌ Помилка: {error}")
            schedule_delete(message, 3)
            schedule_delete(bot_msg, 5)
            return

        # Підписка
        async with AsyncSessionLocal() as session:
            sub_result = await session.execute(
                select(UserSubscription).where(
                    UserSubscription.user_id == message.from_user.id,
                    UserSubscription.channel_id == channel.id
                )
            )
            if not sub_result.scalar_one_or_none():
                # ПЕРЕВІРКА ЛІМІТУ
                status_info = await subscription_service.get_user_status(message.from_user.id, session)
                if not status_info["can_add"]:
                    await message.answer(
                        f"🚫 <b>Ліміт вичерпано</b>\n\n"
                        f"На плані <b>{status_info['tier'].capitalize()}</b> ви можете відстежувати до {status_info['limit']} каналів.\n\n"
                        f"Будь ласка, перейдіть у Mini App, щоб видалити зайві канали або покращити свій план! ✨",
                        reply_markup=get_webapp_kb()
                    )
                    return

                # Визначаємо наступну позицію (черга додавання)
                pos_stmt = select(func.max(UserSubscription.position)).where(UserSubscription.user_id == message.from_user.id)
                pos_res = await session.execute(pos_stmt)
                max_pos = pos_res.scalar()
                next_pos = (max_pos + 1) if max_pos is not None else 0

                session.add(UserSubscription(
                    user_id=message.from_user.id,
                    channel_id=channel.id,
                    position=next_pos
                ))
                await session.commit()
                status = "✅ Підписано!"
                # Запускаємо миттєвий збір новин через монітор
                asyncio.create_task(monitor.track_channel(channel.id))
            else:
                status = "✅ Ви вже підписані"
        
            # Результат
            if config.WEBAPP_URL:
                kb = InlineKeyboardBuilder()
                kb.button(text="📱 Відкрити Pulse", web_app=WebAppInfo(url=config.WEBAPP_URL))
                kb.adjust(1)
                reply_markup = kb.as_markup()
            else:
                reply_markup = None

            bot_msg = await message.answer(
                f"📺 <b>{channel.title}</b>\n"
                f"@{channel.username}\n\n"
                f"{status}",
                reply_markup=reply_markup
            )

            # AI класифікація (якщо категорія ще дефолтна)
            if channel.category == "📰 Події":
                ai_category = await classify_channel(
                    title=channel.title,
                    username=channel.username,
                    sample_text=None
                )
                await channel_service.update_category(channel.id, ai_category)
                await bot_msg.edit_text(
                    f"📺 <b>{channel.title}</b>\n"
                    f"@{channel.username}\n"
                    f"📂 Категорія: <b>{ai_category}</b>\n\n"
                    f"{status}",
                    reply_markup=reply_markup
                )

            schedule_delete(message, 3)
            schedule_delete(bot_msg, 15)
        
    except Exception as e:
        logger.exception(f"ERROR in handle_channel_link: {e}")
        await message.reply(f"Сталася помилка: {e}")


def get_webapp_kb():
    """Допоміжна функція для створення кнопки Mini App"""
    from aiogram.types import WebAppInfo
    if config.WEBAPP_URL:
        kb = InlineKeyboardBuilder()
        kb.button(text="📱 Відкрити Pulse", web_app=WebAppInfo(url=config.WEBAPP_URL))
        return kb.as_markup()
    return None
