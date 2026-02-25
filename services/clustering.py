"""
Pulse Clustering Service — логіка групування новин у сюжети (Stories).
Використовує pgvector для пошуку семантично схожих історій.
"""
from sqlalchemy import select, update
from loguru import logger
from database.connection import AsyncSessionLocal
from database.models import Publication, Story, Category, ChannelCategory
from services.ai_service import get_text_embedding, generate_story_info, get_existing_categories
from pgvector.sqlalchemy import Vector
from datetime import datetime, timezone

# Поріг схожості (Cosine Distance).
# Чим менше, тим суворіше. Для Gemini embeddings:
# 0.0 - ідентичні
# 0.1 - дуже схожі
# 0.2 - одна тема, різні аспекти
# > 0.3 - різні теми
SIMILARITY_THRESHOLD = 0.15

async def cluster_publication(publication_id: int):
    """
    Аналізує публікацію та прив'язує її до існуючої історії або створює нову.
    """
    logger.info(f"Clustering publication {publication_id}...")
    
    async with AsyncSessionLocal() as session:
        # 1. Отримуємо публікацію
        result = await session.execute(
            select(Publication).where(Publication.id == publication_id)
        )
        publication = result.scalar_one_or_none()
        
        if not publication:
            logger.error(f"Publication {publication_id} not found")
            return
        
        if publication.story_id:
            logger.info(f"Publication {publication_id} already in story {publication.story_id}")
            return
        
        # 2. Individual Post Mode: Skip embedding and similarity search
        text_to_embed = publication.content or ""
        embedding = None # Not needed when clustering is disabled

        story_to_link = None
        
        # 4. Линковка або створення
        if story_to_link:
            publication.story_id = story_to_link.id
            publication.category = story_to_link.category # Inherit category
            
            # Оновлюємо час сюжету на час найновішої публікації
            if publication.published_at > story_to_link.last_updated_at:
                story_to_link.last_updated_at = publication.published_at
            status = "linked"
        else:
            # Створюємо нову історію
            # Генеруємо метадані через LLM
            meta = await generate_story_info(text_to_embed)
            
            # Map result to full category with emoji
            from services.ai_service import CATEGORY_MAP
            raw_cat = meta.get("category", "Події")
            
            # Динамічне отримання або створення категорії в БД
            existing_cats = await get_existing_categories()
            # Шукаємо збіг (case insensitive)
            cat_name = raw_cat
            for c in existing_cats:
                if c.lower() == raw_cat.lower():
                    cat_name = c
                    break
            
            # Знаходимо або створюємо категорію в таблиці categories
            stmt_cat = select(Category).where(Category.name == cat_name)
            res_cat = await session.execute(stmt_cat)
            db_cat = res_cat.scalar_one_or_none()
            
            if not db_cat:
                db_cat = Category(name=cat_name, emoji="📰")
                session.add(db_cat)
                await session.flush()
            
            full_cat = f"{db_cat.emoji} {db_cat.name}"

            new_story = Story(
                title=meta.get("title", "Нова подія"),
                summary=meta.get("summary", ""),
                category=full_cat,
                embedding_vector=embedding,
                first_seen_at=publication.published_at, # Використовуємо час публікації
                last_updated_at=publication.published_at,
                status="active"
            )
            session.add(new_story)
            await session.flush()  # Щоб отримати ID
            
            publication.story_id = new_story.id
            publication.category = full_cat # Set direct category
            status = "created"
            logger.info(f"Created new story {new_story.id}: {new_story.title}")

        # 5. Оновлюємо ChannelCategory активність
        if publication.channel_id and db_cat:
            stmt_ch_cat = select(ChannelCategory).where(
                ChannelCategory.channel_id == publication.channel_id,
                ChannelCategory.category_id == db_cat.id
            )
            res_ch_cat = await session.execute(stmt_ch_cat)
            ch_cat = res_ch_cat.scalar_one_or_none()
            
            if not ch_cat:
                ch_cat = ChannelCategory(
                    channel_id=publication.channel_id,
                    category_id=db_cat.id,
                    posts_count=1,
                    last_post_at=publication.published_at
                )
                session.add(ch_cat)
            else:
                ch_cat.posts_count += 1
                if publication.published_at > ch_cat.last_post_at:
                    ch_cat.last_post_at = publication.published_at
            
            logger.info(f"Updated ChannelCategory: channel={publication.channel_id}, cat={db_cat.name}, posts={ch_cat.posts_count}")

        await session.commit()
        return status
