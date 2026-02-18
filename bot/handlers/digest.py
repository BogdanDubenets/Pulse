import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from loguru import logger
from config.settings import config

from services.digest import get_user_digest
from bot.utils import schedule_delete

router = Router()

def digest_keyboard():
    if not config.WEBAPP_URL or not config.WEBAPP_URL.startswith("https"):
        return None
        
    kb = InlineKeyboardBuilder()
    kb.button(text="📱 Читати повністю", web_app=WebAppInfo(url=config.WEBAPP_URL))
    return kb.as_markup()

@router.message(Command("digest", "summary"))
async def cmd_digest(message: Message):
    """
    Генерує дайджест на основі останніх новин.
    """
    logger.info(f"User {message.from_user.id} requested digest.")
    status_msg = await message.answer("⏳ Збираю новини та генерую дайджест (AI)...")
    
    digest_text = await get_user_digest(message.from_user.id)
    
    if digest_text is None:
        await status_msg.edit_text("❌ Ви не підписані на жоден канал. Використовуйте /channels.")
        schedule_delete(status_msg, 7)
        return

    # Відправляємо результат
    await status_msg.delete()
    try:
        await message.answer(digest_text, parse_mode=ParseMode.MARKDOWN, reply_markup=digest_keyboard())
    except Exception as parse_error:
        logger.warning(f"Markdown parse error: {parse_error}. sending as text.")
        await message.answer(digest_text, reply_markup=digest_keyboard())
