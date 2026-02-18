import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config.settings import config
from database.connection import AsyncSessionLocal
from database.models import User, UserSubscription
from sqlalchemy import select
from services.scheduler import send_digests

async def main():
    print("🚀 Starting manual digest sender...")
    
    # 1. Initialize Bot
    bot = Bot(
        token=config.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    try:
        # 2. Get User ID (Optional: pass as arg, or pick first from DB)
        async with AsyncSessionLocal() as session:
            stmt = (
                select(User)
                .join(UserSubscription, User.id == UserSubscription.user_id)
                .limit(1)
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ No users with subscriptions found.")
                return
            
            print(f"🎯 Target User: {user.id} ({user.first_name})")
            
            # 3. Send Digest (simulating Morning digest)
            print("📨 Sending Morgen digest...")
            # We can use the logic from scheduler's send_digests but scoped to one user if we wanted
            # But let's use the actual function if possible, or just call logic manually
            
            # Since send_digests sends to ALL users, we should probably call get_user_digest directly
            # and send it manually to this specific user to avoid spamming everyone if there were more users.
            
            from services.digest import get_user_digest
            
            digest_text = await get_user_digest(user.id)
            
            if digest_text:
                print(f"✅ Digest generated ({len(digest_text)} chars). Sending...")
                greeting = "🌞 **Тестовий дайджест**"
                msg_text = f"{greeting}\n\n{digest_text}"
                
                try:
                    await bot.send_message(user.id, msg_text, parse_mode=ParseMode.MARKDOWN)
                    print("🎉 Message sent via Telegram!")
                except Exception as e:
                    print(f"⚠️ Failed to send Markdown: {e}")
                    # Fallback
                    await bot.send_message(user.id, msg_text)
                    print("🎉 Message sent (Plain text fallback)!")
            else:
                print("⚠️ No digest generated (empty or no news).")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
