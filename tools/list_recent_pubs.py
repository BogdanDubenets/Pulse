import asyncio
from sqlalchemy import select
from database.connection import AsyncSessionLocal
from database.models import Publication, Channel
from datetime import datetime, timezone

async def list_recent_pubs():
    async with AsyncSessionLocal() as session:
        query = select(Publication, Channel.title)\
            .join(Channel, Publication.channel_id == Channel.id)\
            .order_by(Publication.published_at.desc()).limit(20)
        result = await session.execute(query)
        
        print(f"Поточний час сервера (UTC): {datetime.now(timezone.utc)}")
        print("\n--- ОСТАННІ 20 НОВИН У БАЗІ ---")
        for pub, title in result.all():
            print(f"[{pub.published_at}] Ch: {title[:20]:20} | ID: {pub.id} | Content: {pub.content[:50]}...")

if __name__ == "__main__":
    asyncio.run(list_recent_pubs())
