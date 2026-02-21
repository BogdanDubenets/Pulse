
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from sqlalchemy import create_engine, text
import ssl
from config.settings import config

async def resolve_id():
    session = StringSession(config.TELETHON_SESSION)
    client = TelegramClient(session, config.API_ID, config.API_HASH.strip())
    await client.start(phone=config.PHONE_NUMBER)
    try:
        entity = await client.get_entity('lachentyt')
        return entity.id
    finally:
        await client.disconnect()

def update_db(correct_id):
    db_url = config.CLOUD_DATABASE_URL.replace('+asyncpg', '') # Sync engine
    engine = create_engine(db_url, connect_args={"sslmode": "require"})
    
    with engine.connect() as conn:
        # 1. Clear old wrong pubs
        conn.execute(text("DELETE FROM publications WHERE channel_id = 14"))
        # 2. Set correct TG ID
        conn.execute(text(f"UPDATE channels SET telegram_id = {correct_id}, last_scanned_at = NULL WHERE id = 14"))
        conn.commit()
        print(f"✅ DB Updated: Channel 14 set to TG ID {correct_id}")

async def main():
    tg_id = await resolve_id()
    if tg_id:
        update_db(tg_id)

if __name__ == "__main__":
    asyncio.run(main())
