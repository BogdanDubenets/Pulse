import asyncio
import aiohttp
from config.settings import config

async def test_bot():
    token = config.BOT_TOKEN.get_secret_value()
    print(f"Testing token: {token[:10]}...")
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            print(f"getMe response: {data}")
            
        if data.get("ok"):
            # Спробуємо надіслати повідомлення користувачу 461874849
            send_url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": 461874849,
                "text": "🚨 Тестове повідомлення від системи налагодження. Бачите це?"
            }
            async with session.post(send_url, json=payload) as resp:
                send_data = await resp.json()
                print(f"sendMessage response: {send_data}")

if __name__ == "__main__":
    asyncio.run(test_bot())
