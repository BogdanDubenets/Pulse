import re
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

    try:
        async with AsyncSessionLocal() as session:
            # Шукаємо канал у базі
            result = await session.execute(
                select(Channel).where(Channel.telegram_id == chat.id)
            )
            channel = result.scalar_one_or_none()
            
            if channel:
                # Канал вже є — перевіряємо підписку
                sub_result = await session.execute(
                    select(UserSubscription).where(
                        UserSubscription.user_id == message.from_user.id,
                        UserSubscription.channel_id == channel.id
                    )
                )
                subscription = sub_result.scalar_one_or_none()
                
                if not subscription:
                    # Автопідписка
                    session.add(UserSubscription(
                        user_id=message.from_user.id,
                        channel_id=channel.id
                    ))
                    await session.commit()
                    status = "\n\n✅ Підписано!"
                else:
                    status = "\n\n✅ Ви вже підписані"
                
                bot_msg = await message.answer(
                    f"📺 <b>{channel.title}</b>"
                    f"{status}"
                )
                schedule_delete(message, 3)
                schedule_delete(bot_msg, 5)
                return
            
            # Канал новий — створюємо з тимчасовою категорією
            channel = Channel(
                telegram_id=chat.id,
                username=chat.username,
                title=chat.title,
                category="📰 Події",  # Тимчасова, поки AI не визначить
                is_active=True
            )
            session.add(channel)
            await session.commit()
            await session.refresh(channel)
            logger.info(f"New channel created: {chat.title} (db_id={channel.id})")

        # Показуємо повідомлення "аналізую..."
        thinking_msg = await message.answer(
            f"🆕 <b>Новий канал знайдено!</b>\n\n"
            f"📺 <b>{chat.title}</b>\n"
            f"🤖 <i>AI аналізує категорію...</i>"
        )

        # AI класифікація через Gemini
        sample_text = message.text or message.caption or ""
        ai_category = await classify_channel(
            title=chat.title,
            username=chat.username,
            sample_text=sample_text
        )
        
        logger.info(f"AI classified '{chat.title}' → '{ai_category}'")

        # Зберігаємо категорію в БД
        async with AsyncSessionLocal() as session:
            channel = await session.get(Channel, channel.id)
            channel.category = ai_category
            
            # Автоматично підписуємо
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

        # Оновлюємо повідомлення з результатом
        await thinking_msg.edit_text(
            f"✅ <b>Канал додано!</b>\n\n"
            f"📺 <b>{chat.title}</b>\n"
            f"{'@' + chat.username if chat.username else ''}\n\n"
            f"Підписано автоматично! 🟢"
        )
        # Оновлюємо кеш моніторингу миттєво
        await monitor.track_channel(channel.id)
        
        schedule_delete(message, 3)       # Повідомлення юзера
        schedule_delete(thinking_msg, 5)  # Відповідь бота
        
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
        # Перевіряємо чи канал вже є в базі
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Channel).where(Channel.username == username)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Канал вже є — автопідписка
                sub_result = await session.execute(
                    select(UserSubscription).where(
                        UserSubscription.user_id == message.from_user.id,
                        UserSubscription.channel_id == existing.id
                    )
                )
                subscription = sub_result.scalar_one_or_none()
                
                if not subscription:
                    session.add(UserSubscription(
                        user_id=message.from_user.id,
                        channel_id=existing.id
                    ))
                    await session.commit()
                    status = "\n\n✅ Підписано!"
                else:
                    status = "\n\n✅ Ви вже підписані"
                
                # Оновлюємо кеш моніторингу миттєво
                await monitor.track_channel(existing.id)
                
                bot_msg = await message.answer(
                    f"📺 <b>{existing.title}</b>"
                    f"{status}"
                )
                schedule_delete(message, 3)
                schedule_delete(bot_msg, 5)
                return
        
        # Канал новий — резолвимо через Telethon
        thinking_msg = await message.answer(
            f"🔍 <b>Шукаю канал @{username}...</b>\n"
            f"🤖 <i>Зачекайте, аналізую...</i>"
        )
        
        try:
            # Підключаємо Telethon якщо ще не підключений
            if not monitor.client.is_connected():
                await monitor.start()
            
            entity = await monitor.client.get_entity(username)
        except Exception as e:
            logger.error(f"Failed to resolve @{username}: {e}")
            await thinking_msg.edit_text(
                f"❌ <b>Канал @{username} не знайдено</b>\n\n"
                f"Перевірте правильність юзернейму або спробуйте переслати пост з каналу."
            )
            schedule_delete(message, 3)
            schedule_delete(hint, 5)
            return
        
        # Перевіряємо що це канал, а не група або юзер
        from telethon.tl.types import Channel as TelethonChannel
        if not isinstance(entity, TelethonChannel):
            await thinking_msg.edit_text(
                f"⚠️ <b>@{username}</b> — це не канал.\n\n"
                f"Я працюю тільки з Telegram-каналами. Будь ласка, надішліть посилання на канал."
            )
            schedule_delete(message, 3)
            schedule_delete(thinking_msg, 5)
            return
        
        # Створюємо канал у БД
        async with AsyncSessionLocal() as session:
            channel = Channel(
                telegram_id=entity.id,
                username=username,
                title=entity.title,
                category="📰 Події",
                is_active=True
            )
            session.add(channel)
            await session.commit()
            await session.refresh(channel)
            logger.info(f"New channel via link: {entity.title} (db_id={channel.id})")
        
        # AI класифікація
        ai_category = await classify_channel(
            title=entity.title,
            username=username,
            sample_text=None  # Немає тексту поста
        )
        
        logger.info(f"AI classified '{entity.title}' → '{ai_category}'")
        
        # Зберігаємо категорію + автопідписка
        async with AsyncSessionLocal() as session:
            ch = await session.get(Channel, channel.id)
            ch.category = ai_category
            session.add(UserSubscription(
                user_id=message.from_user.id,
                channel_id=channel.id
            ))
            await session.commit()
        
        # Показуємо результат
        await thinking_msg.edit_text(
            f"✅ <b>Канал додано!</b>\n\n"
            f"📺 <b>{entity.title}</b>\n"
            f"@{username}\n\n"
            f"Підписано автоматично! 🟢"
        )
        # Оновлюємо кеш моніторингу миттєво
        await monitor.track_channel(channel.id)
        
        schedule_delete(message, 3)       # Повідомлення юзера
        schedule_delete(thinking_msg, 5)  # Відповідь бота
        
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
