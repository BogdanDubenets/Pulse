import asyncio
from database.connection import AsyncSessionLocal
from database.models import Category
from bot.categories import ALL_CATEGORIES
from sqlalchemy import select
from loguru import logger

async def migrate_categories():
    async with AsyncSessionLocal() as session:
        for full_cat in ALL_CATEGORIES:
            parts = full_cat.split(" ", 1)
            emoji = parts[0]
            name = parts[1] if len(parts) > 1 else full_cat
            
            # Check if exists
            stmt = select(Category).where(Category.name == name)
            res = await session.execute(stmt)
            if res.scalar_one_or_none():
                continue
            
            cat = Category(name=name, emoji=emoji)
            session.add(cat)
            logger.info(f"Adding category: {emoji} {name}")
        
        await session.commit()
        logger.info("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate_categories())
