import asyncio
from sqlalchemy import select, func
from database.connection import AsyncSessionLocal
from database.models import Channel, Publication, UserSubscription

async def check_channels():
    async with AsyncSessionLocal() as session:
        # Get all channels that have subscriptions
        query = (
            select(Channel, func.count(Publication.id).label('pub_count'))
            .outerjoin(Publication, Channel.id == Publication.channel_id)
            .join(UserSubscription, Channel.id == UserSubscription.channel_id)
            .group_by(Channel.id)
        )
        result = await session.execute(query)
        rows = result.all()
        
        print(f"{'ID':<4} | {'Title':<20} | {'Active':<6} | {'Pubs':<5} | {'Last Scanned':<20} | {'Telegram ID'}")
        print("-" * 80)
        for row in rows:
            ch = row.Channel
            pub_count = row.pub_count
            last_scan = ch.last_scanned_at.strftime("%Y-%m-%d %H:%M:%S") if ch.last_scanned_at else "Never"
            print(f"{ch.id:<4} | {ch.title[:20]:<20} | {str(ch.is_active):<6} | {pub_count:<5} | {last_scan:<20} | {ch.telegram_id}")

if __name__ == "__main__":
    asyncio.run(check_channels())
