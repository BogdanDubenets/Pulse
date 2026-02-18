
import asyncio
from database.connection import AsyncSessionLocal
from database.models import UserSubscription, Channel
from sqlalchemy import select, delete

async def fix_subscriptions():
    async with AsyncSessionLocal() as session:
        user_id = 461874849
        # 6 Requested channels:
        # ID 1: Українська правда
        # ID 2: НВ
        # ID 4: Економічна правда
        # ID 5: DOU
        # ID 6: Труха⚡️Київ
        # ID 11: УНИАН
        keep_ids = [1, 2, 4, 5, 6, 11]
        
        # Delete subscriptions not in keep_ids
        stmt = delete(UserSubscription).where(
            UserSubscription.user_id == user_id,
            UserSubscription.channel_id.notin_(keep_ids)
        )
        result = await session.execute(stmt)
        await session.commit()
        print(f"Deleted {result.rowcount} subscriptions. User now has {len(keep_ids)} subscriptions.")

if __name__ == "__main__":
    asyncio.run(fix_subscriptions())
