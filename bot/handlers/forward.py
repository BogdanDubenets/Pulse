import re
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.connection import AsyncSessionLocal
from database.models import Channel, UserSubscription
from sqlalchemy import select
from loguru import logger
from bot.utils import schedule_delete
from database.users import upsert_user

from bot.categories import THEMATIC_CATEGORIES, REGIONAL_CATEGORIES, AUTHOR_CATEGORIES
from services.ai_service import classify_channel
from services.monitor import monitor
from services.channel_service import channel_service

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
            err = await message.reply("Вибачте, я працюю тільки з Телеграм-каналами.")
            schedule_delete(message, 3)
            schedule_delete(err, 5)
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
                session.add(UserSubscription(
                    user_id=message.from_user.id,
                    channel_id=channel.id
                ))
                await session.commit()
                status = "\n\n✅ Підписано!"
                # Запускаємо миттєвий збір новин через монітор
                asyncio.create_task(monitor.track_channel(channel.id))
            else:
                status = "\n\n✅ Ви вже підписані"
            
            # Якщо канал зовсім новий (щойно створений сервісом), запускаємо аналіз категорії
            # Ми можемо перевірити це за часом створення або просто запустити класифікацію для профілактики
            
            bot_msg = await message.answer(
                f"📺 <b>{channel.title}</b>"
                f"{status}"
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
        # Текст без каналу — даємо підказку
        hint = await message.answer(
            "💡 Щоб додати канал — перешліть пост, надішліть @username або t.me/посилання."
        )
        schedule_delete(message, 3)
        schedule_delete(hint, 5)
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
                session.add(UserSubscription(
                    user_id=message.from_user.id,
                    channel_id=channel.id
                ))
                await session.commit()
                status = "✅ Підписано!"
                # Запускаємо миттєвий збір новин через монітор
                asyncio.create_task(monitor.track_channel(channel.id))
            else:
                status = "✅ Ви вже підписані"
        
        # Результат
        bot_msg = await message.answer(
            f"📺 <b>{channel.title}</b>\n"
            f"@{channel.username}\n\n"
            f"{status}"
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
                f"{status}"
            )

        schedule_delete(message, 3)
        schedule_delete(bot_msg, 10)
        
    except Exception as e:
        logger.exception(f"ERROR in handle_channel_link: {e}")
        await message.reply(f"Сталася помилка: {e}")


# ── Ручна зміна категорії (fallback) ──────────────────────────

@router.callback_query(F.data.startswith("fwdtype:"))
async def choose_category_type(callback: CallbackQuery):
    """Крок 1: Обрати тип категорії для ручної зміни"""
    channel_id = int(callback.data.split(":")[1])
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📰 Тематична", callback_data=f"fwdlist:{channel_id}:thematic")
    keyboard.button(text="📍 Регіональна", callback_data=f"fwdlist:{channel_id}:regional")
    keyboard.button(text="✍️ Авторський", callback_data=f"fwdlist:{channel_id}:author")
    keyboard.adjust(2)
    
    await callback.message.edit_text(
        "📂 <b>Змінити категорію</b>\n\nОберіть тип:",
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("fwdlist:"))
async def show_category_list(callback: CallbackQuery):
    """Крок 2: Показати конкретні категорії обраного типу"""
    parts = callback.data.split(":")
    channel_id = int(parts[1])
    cat_type = parts[2]
    
    if cat_type == "thematic":
        categories = THEMATIC_CATEGORIES
        title = "📰 Оберіть тематичну категорію:"
    elif cat_type == "regional":
        categories = REGIONAL_CATEGORIES
        title = "📍 Оберіть регіон:"
    else:
        categories = AUTHOR_CATEGORIES
        title = "✍️ Авторські канали:"
    
    keyboard = InlineKeyboardBuilder()
    for cat in categories:
        keyboard.button(text=cat, callback_data=f"fwdcat:{channel_id}:{cat}")
    keyboard.button(text="⬅️ Назад", callback_data=f"fwdtype:{channel_id}")
    keyboard.adjust(2)
    
    await callback.message.edit_text(title, reply_markup=keyboard.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("fwdcat:"))
async def set_channel_category(callback: CallbackQuery):
    """Крок 3: Зберігаємо обрану категорію"""
    parts = callback.data.split(":", 2)
    channel_id = int(parts[1])
    category = parts[2]
    user_id = callback.from_user.id
    
    logger.info(f"User {user_id} manually set category '{category}' for channel {channel_id}")
    
    try:
        async with AsyncSessionLocal() as session:
            channel = await session.get(Channel, channel_id)
            if not channel:
                await callback.answer("Канал не знайдено", show_alert=True)
                return
            
            channel.category = category
            await session.commit()
            
            logger.info(f"Channel '{channel.title}' → category '{category}' (manual)")
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📚 До каталогу", callback_data="onboarding:catalog")
        keyboard.button(text="🏠 На головну", callback_data="start:back")
        keyboard.adjust(2)
        
        await callback.message.edit_text(
            f"✅ <b>Категорію змінено!</b>\n\n"
            f"📺 <b>{channel.title}</b>\n"
            f"📂 Нова категорія: <b>{category}</b>",
            reply_markup=keyboard.as_markup()
        )
        await callback.answer("Категорію оновлено!")
        
    except Exception as e:
        logger.exception(f"ERROR in set_channel_category: {e}")
        await callback.answer(f"Помилка: {e}", show_alert=True)
