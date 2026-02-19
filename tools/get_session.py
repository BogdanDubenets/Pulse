import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
import os

# Скрипт для конвертації існуючої сесії у STRING_SESSION для Railway
# Запустіть його ЛОКАЛЬНО: python tools/get_session.py

async def main():
    print("🚀 Генератор нової сесії Pulse (Cloud Ready)")
    print("------------------------------------------")
    
    api_id = input("Введіть ваш API_ID [Enter для 34960833]: ") or "34960833"
    api_hash = input("Введіть ваш API_HASH [Enter для 56f04f1192d81339b18e6ef89270a027]: ") or "56f04f1192d81339b18e6ef89270a027"
    
    # Використовуємо порожню StringSession — це змусить Telethon пройти авторизацію заново в пам'яті
    client = TelegramClient(StringSession(), int(api_id), api_hash)
    
    try:
        # start() автоматично запитає телефон і код, якщо ми не авторизовані
        await client.start()
        
        string_session = client.session.save()
        
        print("\n" + "="*50)
        print("✅ АВТОРИЗАЦІЯ УСПІШНА!")
        print("="*50)
        print("\nВаш STRING_SESSION (копіюйте ПОВНІСТЮ):\n")
        print(string_session)
        print("\n" + "="*50)
        print("ІНСТРУКЦІЯ:")
        print("1. Скопіюйте цей рядок.")
        print("2. Йдіть у Railway Dashboard -> Pulse Bot -> Variables.")
        print("3. Оновіть значення TELETHON_SESSION.")
        print("4. Переконайтеся, що бот ЛОКАЛЬНО ВИМКНЕНИЙ.")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Помилка: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
