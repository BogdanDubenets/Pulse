
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import update, text
import ssl
import os
from database.models import Channel
from config.settings import config

async def fix_lachen():
    # 1. Resolve @lachentyt to ID
    session = StringSession(config.TELETHON_SESSION)
    client = TelegramClient(session, config.API_ID, config.API_HASH.strip())
    
    await client.start(phone=config.PHONE_NUMBER)
    try:
        entity = await client.get_entity('lachentyt')
        correct_tg_id = entity.id
        # Більшість каналів у Telethon обробляються з префіксом -100, 
        # але get_entity повертає позитивний ID. 
        # ChannelMonitor у нас підтримує обидва, але за замовчуванням в базі краще тримати чистий ID.
        print(f"✅ Found correct TG ID for @lachentyt: {correct_tg_id} (Title: {entity.title})")
    except Exception as e:
        print(f"❌ Could not resolve @lachentyt: {e}")
        await client.disconnect()
        return

    # 2. Update DB
    db_url = config.CLOUD_DATABASE_URL
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    engine = create_async_engine(db_url, connect_args={
        "ssl": ctx,
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0
    })
    
    Session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with Session() as session:
        # Перевіряємо що там зараз
        res = await session.execute(text("SELECT telegram_id FROM channels WHERE id = 14"))
        old_id = res.scalar()
        print(f"Current TG ID in DB for channel 14: {old_id}")
        
        if str(old_id) == "14":
            print("🚨 ID matches DB Key! This is definitely the bug.")
            await session.execute(
                update(Channel)
                .where(Channel.id == 14)
                .values(telegram_id=correct_tg_id, last_scanned_at=None) # Скидаємо скан щоб завантажив нове
            )
            # Також видалимо старі (невірні) пости
            await session.execute(text("DELETE FROM publications WHERE channel_id = 14"))
            await session.commit()
            print("🚀 DB Updated! Correct TG ID set, old publications cleared.")
        else:
            print("⚠️ TG ID is not 14, but we should update it to the resolved one if different.")
            if old_id != correct_tg_id:
                await session.execute(update(Channel).where(Channel.id == 14).values(telegram_id=correct_tg_id, last_scanned_at=None))
                await session.commit()
                print(f"Updated TG ID from {old_id} to {correct_tg_id}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(fix_lachen())
