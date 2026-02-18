import asyncio
from services.clustering import cluster_publication
from database.connection import AsyncSessionLocal
from database.models import Publication
from sqlalchemy import select, desc
import sys
from loguru import logger

# Configure logger to stdout to see errors
logger.remove()
logger.add(sys.stdout, level="DEBUG")

async def test():
    async with AsyncSessionLocal() as s:
        # Get latest pub without story
        res = await s.execute(select(Publication).where(Publication.story_id == None).order_by(desc(Publication.id)).limit(1))
        pub = res.scalar_one_or_none()
        if not pub:
            # Try any pub
            print("No pubs without story. Trying latest pub.")
            res = await s.execute(select(Publication).order_by(desc(Publication.id)).limit(1))
            pub = res.scalar_one_or_none()
            
        if not pub:
            print("No pubs found.")
            return
        
        print(f"Testing clustering for pub {pub.id}...")
        try:
            await cluster_publication(pub.id)
            print("Clustering finished.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
