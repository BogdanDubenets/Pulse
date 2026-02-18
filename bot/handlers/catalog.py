from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.connection import AsyncSessionLocal
from database.models import Channel, UserSubscription
from sqlalchemy import select, func
from loguru import logger

router = Router()

@router.callback_query(F.data == "onboarding:catalog")
async def show_categories(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} opened catalog")
    try:
        async with AsyncSessionLocal() as session:
            # Отримуємо унікальні категорії
            result = await session.execute(select(Channel.category).distinct().where(Channel.is_active == True))
            categories = [r[0] for r in result.all() if r[0]]
            
        logger.debug(f"Found {len(categories)} categories: {categories}")
        
        keyboard = InlineKeyboardBuilder()
        for cat in categories:
            keyboard.button(text=f"📂 {cat}", callback_data=f"cat:{cat}")
        
        keyboard.button(text="⬅️ Назад", callback_data="start:back")
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            "📚 <b>Каталог каналів</b>\n\nОберіть категорію, щоб переглянути доступні канали:",
            reply_markup=keyboard.as_markup()
        )
        await callback.answer()
    except Exception as e:
        logger.exception(f"ERROR in show_categories: {e}")
        await callback.answer(f"Помилка: {e}", show_alert=True)

@router.callback_query(F.data.startswith("cat:"))
async def show_category_channels(callback: CallbackQuery, override_category: str = None):
    category = override_category or callback.data.split(":")[1]
    user_id = callback.from_user.id
    logger.info(f"User {user_id} viewing category: {category}")
    
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Channel).where(Channel.category == category, Channel.is_active == True).order_by(Channel.title)
            )
            channels = result.scalars().all()
            
            sub_result = await session.execute(
                select(UserSubscription.channel_id).where(UserSubscription.user_id == user_id)
            )
            user_subs = {r[0] for r in sub_result.all()}
        
        logger.debug(f"Found {len(channels)} channels, user has {len(user_subs)} subs")
        
        keyboard = InlineKeyboardBuilder()
        for ch in channels:
            is_sub = ch.id in user_subs
            status_icon = "🟢" if is_sub else "⚪"
            keyboard.button(
                text=f"{status_icon} {ch.title}", 
                callback_data=f"sub:{ch.id}"
            )
        
        keyboard.button(text="⬅️ До категорій", callback_data="onboarding:catalog")
        keyboard.adjust(1)
        
        text = (
            f"📂 Категорія: <b>{category}</b>\n\n"
            f"🟢 — ви підписані\n"
            f"⚪ — ви не підписані\n\n"
            f"<i>Натисніть на назву каналу, щоб змінити статус</i>"
        )
        
        await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
        await callback.answer()
    except Exception as e:
        logger.exception(f"ERROR in show_category_channels: {e}")
        await callback.answer(f"Помилка: {e}", show_alert=True)

@router.callback_query(F.data.startswith("sub:"))
async def toggle_subscription(callback: CallbackQuery):
    channel_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    logger.info(f"User {user_id} toggling subscription for channel {channel_id}")
    
    try:
        async with AsyncSessionLocal() as session:
            # Отримуємо канал та підписку
            channel = await session.get(Channel, channel_id)
            if not channel:
                await callback.answer("Канал не знайдено", show_alert=True)
                return

            result = await session.execute(
                select(UserSubscription).where(
                    UserSubscription.user_id == user_id, 
                    UserSubscription.channel_id == channel_id
                )
            )
            subscription = result.scalar_one_or_none()
            
            if subscription:
                await session.delete(subscription)
                action_msg = f"❌ Відписано від {channel.title}"
            else:
                new_sub = UserSubscription(user_id=user_id, channel_id=channel_id)
                session.add(new_sub)
                action_msg = f"✅ Підписано на {channel.title}"
            
            await session.commit()
            category = channel.category
        
        logger.info(f"Subscription toggled: {action_msg}")
        await callback.answer(action_msg)
        
        # Оновлюємо список каналів у повідомленні
        await show_category_channels(callback, override_category=category)
    except Exception as e:
        logger.exception(f"ERROR in toggle_subscription: {e}")
        await callback.answer(f"Помилка: {e}", show_alert=True)
