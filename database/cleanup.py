from datetime import datetime, timedelta
from sqlalchemy import delete
from database.connection import AsyncSessionLocal
from database.models import Story
from loguru import logger

async def cleanup_old_data(hours: int = 24):
    """
    Видаляє історії, які не оновлювалися більше вказаної кількості годин.
    Завдяки ForeignKey(ondelete="CASCADE"), пов'язані публікації
    та аналітика видаляться автоматично.
    """
    threshold = datetime.utcnow() - timedelta(hours=hours)
    
    try:
        async with AsyncSessionLocal() as session:
            # Видаляємо історії
            stmt = delete(Story).where(Story.last_updated_at < threshold)
            result = await session.execute(stmt)
            await session.commit()
            
            deleted_count = result.rowcount
            if deleted_count > 0:
                logger.info(f"🧹 Очищення бази: видалено {deleted_count} застарілих історій (старіше {hours} год).")
            else:
                logger.debug("🧹 Очищення бази: застарілих даних не знайдено.")
                
            return deleted_count
            
    except Exception as e:
        logger.error(f"❌ Помилка при очищенні бази даних: {e}")
        return 0

if __name__ == "__main__":
    import asyncio
    asyncio.run(cleanup_old_data())
