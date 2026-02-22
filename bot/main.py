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
    from bot.handlers import start, catalog, forward, channels, digest, billing
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(channels.router)
    dp.include_router(digest.router)
    dp.include_router(billing.router) # Billing handlers for payments
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
        BotCommand(command="start", description="Почати роботу з ботом"),
        BotCommand(command="add", description="Додати канал посиланням"),
        BotCommand(command="channels", description="Мої канали"),
        BotCommand(command="summary", description="Отримати дайджест зараз"),
        BotCommand(command="settings", description="Налаштування"),
        BotCommand(command="help", description="Довідка"),
        BotCommand(command="feedback", description="Залишити відгук"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    logger.info("Bot commands menu set.")

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
