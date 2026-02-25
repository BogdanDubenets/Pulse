import html
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from config.settings import config
from database.users import upsert_user

router = Router()


def main_keyboard():
    """Радикально проста клавіатура: ТІЛЬКИ ОДНА КНОПКА"""
    kb = InlineKeyboardBuilder()
    if config.WEBAPP_URL:
        kb.button(text="📱 Відкрити Pulse", web_app=WebAppInfo(url=config.WEBAPP_URL))
    return kb.as_markup()


def welcome_text(first_name: str) -> str:
    """Текст привітання: Catchy & Premium"""
    return (
        f"Привіт, {first_name}! 👋\n\n"
        "Pulse 💓 — твій інтелектуальний фільтр новин.\n\n"
        "Я перетворюю хаос із сотень каналів на лаконічний AI-дайджест. Економ час для головного, а новини залиш мені.\n\n"
        "Тисни кнопку нижче, щоб спробувати майбутнє!"
    )


@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject, bot: Bot):
    user = message.from_user
    logger.info(f"User {user.id} started the bot with args: {command.args}")
    
    referrer_id = None
    if command.args and command.args.startswith("aff_"):
        try:
            potential_ref = int(command.args.split("_")[1])
            if potential_ref != user.id: # Не можна запросити самого себе
                referrer_id = potential_ref
                logger.info(f"User {user.id} referred by {referrer_id}")
        except (IndexError, ValueError):
            pass

    # Реєстрація/оновлення користувача в БД
    await upsert_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        referrer_id=referrer_id
    )
    
    try:
        fn = user.first_name if user else "Друже"
        # Відправляємо повідомлення та примусово видаляємо будь-яку стару Reply-клавіатуру
        from aiogram.types import ReplyKeyboardRemove
        await message.answer(welcome_text(fn), reply_markup=main_keyboard())
        
        # Встановлюємо кнопку меню (лівий нижній кут) індивідуально для юзера
        from aiogram.types import MenuButtonWebApp, WebAppInfo
        if config.WEBAPP_URL:
            await bot.set_chat_menu_button(
                chat_id=message.chat.id,
                menu_button=MenuButtonWebApp(text="Pulse 📱", web_app=WebAppInfo(url=config.WEBAPP_URL))
            )
            
        logger.info(f"Start message sent to {user.id}")
    except Exception as e:
        logger.exception(f"FAIL in cmd_start: {e}")
