import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from config.settings import config
from loguru import logger

async def generate_string_session():
    print("\n--- Telethon String Session Generator ---")
    print("Цей скрипт допоможе вам отримати рядок сесії для роботи в хмарі.")
    
    if not config.API_ID or not config.API_HASH:
        logger.error("API_ID або API_HASH не налаштовані в .env!")
        return

    async with TelegramClient(StringSession(), config.API_ID, config.API_HASH) as client:
        session_str = client.session.save()
        print("\n✅ Успішний вхід!")
        print("-" * 50)
        print("ВАШ ТЕКСТ СЕСІЇ (Скопіюйте його повністю):")
        print("-" * 50)
        print(session_str)
        print("-" * 50)
        print("\nДодайте цей рядок у Railway як змінну оточення TELETHON_SESSION")

if __name__ == "__main__":
    asyncio.run(generate_string_session())
