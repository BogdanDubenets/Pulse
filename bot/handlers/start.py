```python
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
    """Текст привітання: Ultra Minimal"""
    return (
        f"Привіт, {first_name}! 👋\n\n"
        "Pulse — твій персональний AI-дайджест новин.\n"
        "Натисни кнопку нижче, щоб керувати підписками."
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
        first_name=user.first_name,
        username=user.username,
        language_code=user.language_code,
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
        await message.answer("Сталася помилка. Спробуйте /start ще раз.")


@router.callback_query(F.data == "start:back")
async def back_to_start(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} returned to start")
    fn = callback.from_user.first_name or "Друже"
    await callback.message.edit_text(welcome_text(fn), reply_markup=main_keyboard())
    await callback.answer()


# ── Інструкції додавання каналу ────────────────────────────────

@router.message(Command("add"))
async def cmd_add(message: Message):
    """Команда /add — інструкція як додати канал"""
    await message.answer(add_channel_text(), reply_markup=add_channel_keyboard())


@router.callback_query(F.data == "onboarding:add")
async def cb_add(callback: CallbackQuery):
    await callback.message.edit_text(add_channel_text(), reply_markup=add_channel_keyboard())
    await callback.answer()


def add_channel_text() -> str:
    return (
        "➕ <b>Додати канал</b>\n\n"
        "Є 3 способи:\n\n"
        "📤 <b>Переслати пост</b>\n"
        "Відкрий канал → обери будь-який пост → Forward мені\n\n"
        "🔗 <b>Надіслати посилання</b>\n"
        "Просто напиши або встав:\n"
        "• <code>https://t.me/channel</code>\n"
        "• <code>t.me/channel</code>\n\n"
        "✍️ <b>Написати юзернейм</b>\n"
        "• <code>@channel</code>\n\n"
        "💡 <i>Я автоматично розпізнаю канал і додам його до твого списку!</i>"
    )


def add_channel_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="start:back")
    kb.adjust(1)
    return kb.as_markup()


# ── Допомога ───────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(help_text(), reply_markup=help_keyboard())


@router.callback_query(F.data == "onboarding:help")
async def cb_help(callback: CallbackQuery):
    await callback.message.edit_text(help_text(), reply_markup=help_keyboard())
    await callback.answer()


def help_text() -> str:
    return (
        "❓ <b>Допомога</b>\n\n"
        "📌 <b>Команди:</b>\n"
        "/start — Головне меню\n"
        "/add — Додати канал\n"
        "/channels — Мої канали\n"
        "/summary — Дайджест (скоро)\n"
        "/help — Ця довідка\n"
        "/feedback — Залишити відгук\n\n"
        "📌 <b>Як це працює:</b>\n"
        "1. Додай канали, які читаєш\n"
        "2. Я стежу за новинами 24/7\n"
        "3. Отримуй дайджест з головним\n\n"
        "💬 Питання? Напиши /feedback"
    )


def help_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Додати канал", callback_data="onboarding:add")
    kb.button(text="⬅️ Назад", callback_data="start:back")
    kb.adjust(1)
    return kb.as_markup()


# ── Обробка невідомого тексту ──────────────────────────────────

@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    """Заглушка для неактивних кнопок"""
    await callback.answer()
