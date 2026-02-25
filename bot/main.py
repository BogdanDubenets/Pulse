import asyncio
import sys
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.settings import config

async def main():
    # Налаштування логування
    logger.remove()
    logger.add(sys.stdout, level="DEBUG")
    logger.info("Starting Pulse Bot...")

    # Ініціалізація бота та диспетчера
    bot = Bot(
        token=config.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Підключення роутерів
    from bot.handlers import start, forward
    dp.include_router(start.router)
    dp.include_router(forward.router)  # Останнім — бо ловить текстові повідомлення
    
    
    logger.info("Bot is ready to poll!")
    
    # Запуск моніторингу у фоні
    from services.monitor import monitor
    monitor_task = asyncio.create_task(monitor.run_monitoring())

    # Запуск планувальника ранкових дайджестів (8:00)
    from services.scheduler import run_scheduler
    scheduler_task = asyncio.create_task(run_scheduler(bot))
    
    from aiogram.types import BotCommand, BotCommandScopeDefault

    # Налаштування меню команд
    commands = [
        BotCommand(command="start", description="Запустити Pulse"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    
    # Налаштування глобальної кнопки меню (WebApp)
    from aiogram.types import MenuButtonWebApp, WebAppInfo
    if config.WEBAPP_URL:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="Pulse 📱", web_app=WebAppInfo(url=config.WEBAPP_URL))
        )
    
    # Налаштування описів бота
    await bot.set_my_description(
        "Pulse 💓 — твій інтелектуальний фільтр новин.\n\n"
        "Я перетворюю хаос із сотень каналів на лаконічний AI-дайджест. Економ час для головного, а новини залиш мені."
    )
    await bot.set_my_short_description(
        "Pulse 💓 — AI-дайджест твоїх новин. Економ час, читай головне!"
    )

    logger.info("Bot commands, descriptions and menu button set.")

    try:
        # Пропускаємо старі накопичені запити при запуску
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Error during polling: {e}")
    finally:
        # Зупиняємо моніторинг коректно
        await monitor.stop()
        if not monitor_task.done():
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
                
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
