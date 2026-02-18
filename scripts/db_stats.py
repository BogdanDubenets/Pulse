import asyncio
from sqlalchemy import select, func, desc
from database.connection import AsyncSessionLocal
from database.models import Channel, Publication, Story

async def stats():
    try:
        async with AsyncSessionLocal() as s:
            # Counts
            c_count = await s.scalar(select(func.count(Channel.id)))
            p_count = await s.scalar(select(func.count(Publication.id)))
            s_count = await s.scalar(select(func.count(Story.id)))
            
            print(f"📊 Statistics:")
            print(f"Channels: {c_count}")
            print(f"Publications: {p_count}")
            print(f"Stories: {s_count}")
            print("-" * 20)
            
            # Latest Stories
            print("🆕 Latest Stories:")
            stories = await s.execute(select(Story).order_by(desc(Story.first_seen_at)).limit(5))
            for st in stories.scalars():
                print(f"- [{st.first_seen_at.strftime('%H:%M')}] {st.title} ({st.category})")
                
            print("-" * 20)
            # Latest Publications
            print("📝 Latest Publications:")
            pubs = await s.execute(select(Publication).order_by(desc(Publication.published_at)).limit(5))
            for p in pubs.scalars():
                # Get channel
                ch = await s.get(Channel, p.channel_id)
                ch_title = ch.title if ch else "?"
                content = p.content.replace('\n', ' ') if p.content else "No content"
                print(f"- [{p.published_at.strftime('%H:%M')}] {ch_title}: {content[:50]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(stats())
