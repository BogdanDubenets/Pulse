import asyncio
import os
import sys
from telethon import TelegramClient

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config.settings import config

async def run_test():
    if config.TELETHON_SESSION:
        from telethon.sessions import StringSession
        session = StringSession(config.TELETHON_SESSION)
    else:
        session = 'session/pulse_monitor'
    client = TelegramClient(session, config.API_ID, config.API_HASH)
    await client.start(phone=config.PHONE_NUMBER)
    for channel in ['h_kyiv', 'ainua']:
        try:
            messages = await client.get_messages(channel, limit=3)
            for m in messages:
                print(f"[{channel}] {m.date} | {len(m.message or '')} chars")
        except Exception as e:
            print(f"[{channel}] Error: {e}")
    await client.disconnect()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_test())
