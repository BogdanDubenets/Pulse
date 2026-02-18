import asyncio
import sys
import os

# Додаємо кореневу папку проекту в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import AsyncSessionLocal
from database.models import User, UserSubscription
from sqlalchemy import select
from services.digest import get_user_digest_data

async def main():
    async with AsyncSessionLocal() as session:
        # 1. Отримуємо будь-якого користувача з підписками
        stmt = (
            select(User)
            .join(UserSubscription, User.id == UserSubscription.user_id)
            .limit(1)
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ No users with subscriptions found in DB.")
            return

        print(f"User found: {user.id} ({user.first_name})")
        
        # 2. Тестуємо get_user_digest_data
        print(f"Testing get_user_digest_data for user {user.id}...")
        try:
            data = await get_user_digest_data(user.id, hours=48) # Беремо більше годин для тесту
            
            if "error" in data:
                print(f"❌ Error: {data['error']}")
            else:
                print("\n✅ Digest Data Generated Successfully!")
                print(f"Top Stories: {len(data['top_stories'])}")
                for s in data['top_stories']:
                    print(f"  - [{s['id']}] {s['title']} (Score: {s['score']:.2f})")
                    print(f"    Sources: {', '.join(s['sources'])}")
                
                print(f"\nOther News: {len(data['other_news'])}")
                for n in data['other_news']:
                    print(f"  - [{n['id']}] {n['text'][:50]}... ({n['channel']})")
                
                print(f"\nStats: {data['stats']}")

        except Exception as e:
            print(f"❌ Exception during digest generation: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
