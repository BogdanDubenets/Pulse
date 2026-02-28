import asyncio
import os
import sys
from telethon import TelegramClient

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config.settings import config
from services.monitor import ChannelMonitor

async def test_fetch():
    print("Testing fetch from lachentyt...")
    if config.TELETHON_SESSION:
        from telethon.sessions import StringSession
        session = StringSession(config.TELETHON_SESSION)
    else:
        session = 'session/pulse_monitor'

    client = TelegramClient(session, config.API_ID, config.API_HASH)
    await client.start(phone=config.PHONE_NUMBER)
    print("Telethon connected.")

    # Initialize a mock monitor to use its is_ad method
    # It requires passing a client, we'll pass ours
    monitor = ChannelMonitor()
    monitor.client = client

    try:
        messages = await client.get_messages('lachentyt', limit=5)
        print(f"Fetched {len(messages)} messages.")
        for m in messages:
            if m.message:
                is_ad = monitor.is_ad(m.message, 'lachentyt')
                text_preview = m.message[:50].replace('\n', ' ')
                print(f"[{m.date}] AD={is_ad} | {text_preview}...")
            else:
                print(f"[{m.date}] (No text)")
    except Exception as e:
        print(f"Error fetching messages: {e}")

    await client.disconnect()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_fetch())
