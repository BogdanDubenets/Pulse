import asyncio
from sqlalchemy import update, select
from database.connection import AsyncSessionLocal
from database.models import Channel, UserSubscription
from services.monitor import monitor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def kickstart():
    logger.info("Starting force kickstart for monitoring...")
    
    async with AsyncSessionLocal() as session:
        # 1. Reset last_scanned_at for channels with subscribers that have 0 posts or haven't been scanned recently
        # This will trigger the new auto-scan logic in monitor.py
        query = select(Channel).join(UserSubscription).where(Channel.is_active == True)
        result = await session.execute(query)
        channels = result.scalars().all()
        
        for ch in channels:
            # We reset it to None to force the monitor to pick it up and scan for 24h
            ch.last_scanned_at = None
            logger.info(f"Resetting last_scanned_at for: {ch.title} (ID: {ch.id})")
        
        await session.commit()
    
    logger.info("Kickstart complete. The monitoring service (if running) will pick these up within 60 seconds.")
    logger.info("Note: If the monitoring service is NOT running on this machine, you need to restart it on Railway.")

if __name__ == "__main__":
    asyncio.run(kickstart())
