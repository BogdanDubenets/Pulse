"""
Pulse Clustering Service — логіка групування новин у сюжети (Stories).
Використовує pgvector для пошуку семантично схожих історій.
"""
from sqlalchemy import select, update
from loguru import logger
from database.connection import AsyncSessionLocal
from database.models import Publication, Story
from services.ai_service import get_text_embedding, generate_story_info
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
        
        # 2. Генеруємо вектор
        # Використовуємо заголовок (якщо є, в telegram це перші рядки) і текст
        text_to_embed = publication.content or ""
        embedding = await get_text_embedding(text_to_embed)
        
        if not embedding:
            logger.warning(f"Failed to generate embedding for pub {publication_id}")
            return

        # 3. Вимикаємо пошук схожих історій (Individual Post Mode)
        # Кожна публікація отримує власну Story.
        story_to_link = None
        logger.info("Individual Post Mode: Skipping similarity search.")
        
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
            full_cat = CATEGORY_MAP.get(raw_cat, f"📰 {raw_cat}")

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

        await session.commit()
        return status
