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
    """Показує повідомлення з посиланням на Mini App для керування каналами"""
    from config.settings import config
    
    text = (
        "📋 <b>Керування каналами</b>\n\n"
        "Переглянути список ваших підписок та змінити їх можна у нашому Mini App.\n\n"
        "Це зручніше, швидше та наочніше! ✨"
    )
    
    kb = InlineKeyboardBuilder()
    if config.WEBAPP_URL:
        kb.button(text="📱 Відкрити Pulse", web_app=WebAppInfo(url=config.WEBAPP_URL))
    
    kb.button(text="⬅️ Назад", callback_data="start:back")
    kb.adjust(1)
    
    if callback:
        await callback.message.edit_text(text, reply_markup=kb.as_markup())
    elif message:
        await message.answer(text, reply_markup=kb.as_markup())
