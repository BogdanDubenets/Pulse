import asyncio
from telethon import TelegramClient
from config.settings import config
from loguru import logger
import os

async def init_session():
    # Створюємо папку для сесій
    os.makedirs('session', exist_ok=True)
    
    logger.info(f"Initializing Telegram session for {config.PHONE_NUMBER}...")
    
    client = TelegramClient(
        'session/pulse_monitor', 
        config.API_ID, 
        config.API_HASH.strip()
    )
    
    await client.start(phone=config.PHONE_NUMBER)
    
    me = await client.get_me()
    logger.info(f"Successfully logged in as {me.first_name} (@{me.username})")
    logger.info("Session file created in 'session/pulse_monitor.session'")
    
    await client.disconnect()

if __name__ == "__main__":
    if config.PHONE_NUMBER == "your_phone_number_here":
        logger.error("Please set your PHONE_NUMBER in .env file first!")
    else:
        asyncio.run(init_session())
