"""
Хендлер для перегляду підписок користувача: /channels та кнопка "Мої канали"
З можливістю відписки від каналів.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.connection import AsyncSessionLocal
from database.models import Channel, UserSubscription
from sqlalchemy import select, delete
from loguru import logger
from bot.utils import schedule_delete

router = Router()


@router.message(Command("channels"))
async def cmd_channels(message: Message):
    """Команда /channels — показати підписки"""
    await show_user_channels(message.from_user.id, message=message)


@router.callback_query(F.data == "my_channels")
async def cb_channels(callback: CallbackQuery):
    """Кнопка 'Мої канали' — показати підписки"""
    await show_user_channels(callback.from_user.id, callback=callback)
    await callback.answer()


async def show_user_channels(user_id: int, message: Message = None, callback: CallbackQuery = None):
    """Показує список каналів, на які підписаний користувач"""
    try:
        async with AsyncSessionLocal() as session:
            # Отримуємо всі підписки з JOIN на канали
            result = await session.execute(
                select(Channel)
                .join(UserSubscription, UserSubscription.channel_id == Channel.id)
                .where(UserSubscription.user_id == user_id)
                .order_by(Channel.title)
            )
            channels = result.scalars().all()
        
        keyboard = InlineKeyboardBuilder()
        
        if not channels:
            text = (
                "📋 <b>Мої канали</b>\n\n"
                "У вас ще немає підписок.\n\n"
                "💡 <b>Як додати канал:</b>\n"
                "• Перешліть пост з каналу\n"
                "• Надішліть посилання: <code>t.me/channel</code>\n"
                "• Або юзернейм: <code>@channel</code>"
            )
            keyboard.button(text="➕ Додати канал", callback_data="onboarding:add")
            keyboard.button(text="🏠 На головну", callback_data="start:back")
            keyboard.adjust(1)
        else:
            lines = [f"📋 <b>Мої канали</b> ({len(channels)})\n"]
            for i, ch in enumerate(channels, 1):
                username_str = f" · @{ch.username}" if ch.username else ""
                lines.append(f"{i}. 📺 <b>{ch.title}</b>{username_str}")
            
            lines.append(f"\n💡 Натисніть ❌ щоб відписатися")
            text = "\n".join(lines)
            
            # Кнопки відписки для кожного каналу
            for ch in channels:
                short_title = ch.title[:20] + "…" if len(ch.title) > 20 else ch.title
                keyboard.button(
                    text=f"❌ {short_title}", 
                    callback_data=f"unsub:{ch.id}"
                )
            keyboard.button(text="🏠 На головну", callback_data="start:back")
            keyboard.adjust(1)
        
        logger.info(f"User {user_id} viewed channels: {len(channels)} subscriptions")
        
        if callback:
            await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
        elif message:
            await message.answer(text, reply_markup=keyboard.as_markup())
            
    except Exception as e:
        logger.exception(f"ERROR in show_user_channels: {e}")
        error_text = "Сталася помилка при завантаженні каналів."
        if callback:
            await callback.answer(error_text, show_alert=True)
        elif message:
            await message.answer(error_text)


# ── Відписка від каналу ────────────────────────────────────────

@router.callback_query(F.data.startswith("unsub:"))
async def unsubscribe_channel(callback: CallbackQuery):
    """Відписка від каналу"""
    channel_id = int(callback.data.split(":")[1])
    
    try:
        async with AsyncSessionLocal() as session:
            # Отримуємо назву каналу
            ch_result = await session.execute(
                select(Channel).where(Channel.id == channel_id)
            )
            channel = ch_result.scalar_one_or_none()
            
            # Видаляємо підписку
            await session.execute(
                delete(UserSubscription).where(
                    UserSubscription.user_id == callback.from_user.id,
                    UserSubscription.channel_id == channel_id
                )
            )
            await session.commit()
        
        title = channel.title if channel else "канал"
        logger.info(f"User {callback.from_user.id} unsubscribed from '{title}' (id={channel_id})")
        
        await callback.answer(f"❌ Відписано від {title}")
        
        # Оновлюємо список каналів
        await show_user_channels(callback.from_user.id, callback=callback)
        
    except Exception as e:
        logger.exception(f"ERROR in unsubscribe_channel: {e}")
        await callback.answer(f"Помилка: {e}", show_alert=True)
