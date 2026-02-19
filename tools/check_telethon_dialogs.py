from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import os
from config.settings import config
import logging

logging.basicConfig(level=logging.INFO)

async def check_dialogs():
    if config.TELETHON_SESSION:
        session = StringSession(config.TELETHON_SESSION)
    else:
        session = 'session/pulse_monitor'
    
    client = TelegramClient(session, config.API_ID, config.API_HASH.strip())
    
    await client.connect()
    if not await client.is_user_authorized():
        print("Bot user not authorized!")
        return

    print("--- Dialogs ---")
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            print(f"Channel: {dialog.title} | ID: {dialog.id} | Username: {dialog.username}")
            
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check_dialogs())
