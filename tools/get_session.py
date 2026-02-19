from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os

# Скрипт для отримання TELETHON_SESSION для Railway
# Запустіть його ЛОКАЛЬНО: python tools/get_session.py

def main():
    api_id = input("Введіть ваш API_ID: ")
    api_hash = input("Введіть ваш API_HASH: ")
    
    with TelegramClient(StringSession(), int(api_id), api_hash) as client:
        print("\nВаш STRING_SESSION (скопіюйте його ПОВНІСТЮ):\n")
        print(client.session.save())
        print("\nДодайте цей рядок у змінні Railway як TELETHON_SESSION\n")

if __name__ == "__main__":
    main()
