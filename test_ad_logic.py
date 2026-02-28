import asyncio
import os
import sys
from telethon import TelegramClient

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config.settings import config
from services.monitor import ChannelMonitor

async def run_detailed_test():
    print("Testing fetch from lachentyt...")
    if config.TELETHON_SESSION:
        from telethon.sessions import StringSession
        session = StringSession(config.TELETHON_SESSION)
    else:
        session = 'session/pulse_monitor'

    client = TelegramClient(session, config.API_ID, config.API_HASH)
    await client.start(phone=config.PHONE_NUMBER)

    monitor = ChannelMonitor()
    monitor.client = client

    try:
        messages = await client.get_messages('lachentyt', limit=10)
        print(f"Fetched {len(messages)} messages.")
        for m in messages:
            if m.message:
                is_ad = await monitor.is_ad(m.message, 15) # lachentyt is channel ID 15 in my local run
                text_preview = m.message[:150].replace('\n', ' ')
                print(f"[{m.date}] AD={is_ad} | {text_preview}")
                if is_ad:
                    for marker in ["#реклама", "#promo", "реклама", "за посиланням", "купити", "знижка", "підписуйтесь", "реєструйтеся", "зареєструватися", "гроші", "казино", "ставки", "промокод", "заробіток", "виплати", "крипта", "біткоїн", "bitcoin", "курс валют тут", "дивіться за посиланням", "переходьте", "підпишись", "еко-система", "інвестування", "безкоштовно", "дарма", "акція", "розіграш", "айфон", "інтим", "бутик", "шоп", "18+", "🔞", "замовити", "магазин", "знижк", "промокод", "ловіть", "тільки сьогодні", "t.me/+", "t.me/joinchat", "#промо"]:
                        if marker in m.message.lower():
                            print(f"  -> Triggered by: '{marker}'")
            else:
                print(f"[{m.date}] (No text)")
        
        print("\nTesting korrespondent_net...")
        messages = await client.get_messages('korrespondent_net', limit=5)
        for m in messages:
            if m.message:
                is_ad = await monitor.is_ad(m.message, 43)
                text_preview = m.message[:100].replace('\n', ' ')
                print(f"[{m.date}] AD={is_ad} | {text_preview}")
                if is_ad:
                    for marker in ["#реклама", "#promo", "реклама", "за посиланням", "купити", "знижка", "підписуйтесь", "реєструйтеся", "зареєструватися", "гроші", "казино", "ставки", "промокод", "заробіток", "виплати", "крипта", "біткоїн", "bitcoin", "курс валют тут", "дивіться за посиланням", "переходьте", "підпишись", "еко-система", "інвестування", "безкоштовно", "дарма", "акція", "розіграш", "айфон", "інтим", "бутик", "шоп", "18+", "🔞", "замовити", "магазин", "знижк", "промокод", "ловіть", "тільки сьогодні", "t.me/+", "t.me/joinchat", "#промо"]:
                        if marker in m.message.lower():
                            print(f"  -> Triggered by: '{marker}'")

    except Exception as e:
        print(f"Error: {e}")

    await client.disconnect()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_detailed_test())
