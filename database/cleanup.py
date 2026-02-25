from datetime import datetime, timedelta, timezone
from sqlalchemy import delete, update, select
from database.connection import AsyncSessionLocal
from database.models import Story
from loguru import logger

async def cleanup_old_data(hours: int = 24):
    """
    Видаляє історії, які не оновлювалися більше вказаної кількості годин.
    Завдяки ForeignKey(ondelete="CASCADE"), пов'язані публікації
    та аналітика видаляться автоматично.
    """
    threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    try:
        async with AsyncSessionLocal() as session:
            from database.models import ChannelCategory, Publication, Story
            from sqlalchemy import func, select, update, delete
            
            # 1. Спершу видаляємо публікації, які старші за поріг (незалежно від сюжетів)
            pub_del_stmt = delete(Publication).where(Publication.published_at < threshold)
            pub_res = await session.execute(pub_del_stmt)
            deleted_pubs = pub_res.rowcount

            # 2. Видаляємо історії, які не оновлювалися
            story_del_stmt = delete(Story).where(Story.last_updated_at < threshold)
            story_res = await session.execute(story_del_stmt)
            deleted_stories = story_res.rowcount
            
            # 3. Оновлюємо статистику ChannelCategory
            # ... (решта логіки без змін)
            # Ми перераховуємо к-сть постів для всіх записів, щоб вони були синхронні з 24г вікном
            # Отримуємо актуальні лічильники
            stats_stmt = (
                select(Publication.channel_id, Publication.category, func.count(Publication.id))
                .where(Publication.published_at >= threshold, Publication.category != None)
                .group_by(Publication.channel_id, Publication.category)
            )
            stats_res = await session.execute(stats_stmt)
            active_stats = stats_res.all()
            
            # Скидаємо всі лічильники в 0 перед оновленням (або видаляємо ті, де 0)
            await session.execute(update(ChannelCategory).values(posts_count=0))
            
            # Отримаємо категорії для маппінгу (як у backfill)
            from database.models import Category
            cat_stmt = select(Category)
            cat_res = await session.execute(cat_stmt)
            all_cats_full = {f"{c.emoji} {c.name}".lower(): c.id for c in cat_res.scalars().all()}
            
            updated_count = 0
            for ch_id, pub_cat, count in active_stats:
                cat_id = all_cats_full.get(pub_cat.lower())
                if cat_id:
                    await session.execute(
                        update(ChannelCategory)
                        .where(ChannelCategory.channel_id == ch_id, ChannelCategory.category_id == cat_id)
                        .values(posts_count=count)
                    )
                    updated_count += 1
            
            # Видаляємо записи з 0 постів, щоб закривати неактивні категорії
            await session.execute(delete(ChannelCategory).where(ChannelCategory.posts_count == 0))
            
            await session.commit()
            
            if deleted_stories > 0 or updated_count > 0:
                logger.info(f"🧹 Очищення бази: видалено {deleted_stories} застарілих історій. Оновлено {updated_count} записів активності.")
            else:
                logger.debug("🧹 Очищення бази: застарілих даних не знайдено.")
                
            return deleted_stories
            
    except Exception as e:
        logger.error(f"❌ Помилка при очищенні бази даних: {e}")
        return 0

if __name__ == "__main__":
    import asyncio
    asyncio.run(cleanup_old_data())
