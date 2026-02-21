import re
from datetime import datetime, timedelta
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload, defer
from database.connection import AsyncSessionLocal
from database.models import Story, Publication, Channel, UserSubscription
from loguru import logger
from services.ai_service import generate_daily_digest

def clean_markdown(text: str) -> str:
    """Видаляє Markdown-посилання [текст](url), залишаючи лише 'текст'."""
    if not text: return ""
    # Спочатку прибираємо [текст](url) -> текст
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Прибираємо подвійні зірочки
    text = text.replace("**", "")
    return text.strip()

async def get_user_digest_data(
    user_id: int, 
    hours: int = 120, 
    group_by: str = "category", 
    pinned_categories: list[str] = None,
    limit: int = 20,
    offset: int = 0
) -> dict:
    """
    Повертає структуровані дані дайджесту для Mini App / API.
    """
    async with AsyncSessionLocal() as session:
        # 1. Отримуємо ID каналів користувача
        stmt_subs = select(UserSubscription.channel_id).where(UserSubscription.user_id == user_id)
        result_subs = await session.execute(stmt_subs)
        user_channel_ids = list(result_subs.scalars().all())
        
        if not user_channel_ids:
            return {"error": "no_subscriptions"}

        from datetime import timezone
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)

        # 2. Отримуємо Stories
        stmt_stories = (
            select(Story)
            .options(defer(Story.embedding_vector))
            .join(Publication, Story.id == Publication.story_id)
            .where(
                Story.last_updated_at >= time_threshold,
                Publication.channel_id.in_(user_channel_ids)
            )
        )
        
        # Додаємо фільтрацію за обраними категоріями/каналами
        if pinned_categories:
            if group_by == "category":
                stmt_stories = stmt_stories.where(Story.category.in_(pinned_categories))
            elif group_by == "channel":
                stmt_stories = stmt_stories.join(Channel, Publication.channel_id == Channel.id).where(Channel.title.in_(pinned_categories))

        stmt_stories = (
            stmt_stories.distinct()
            .order_by(desc(Story.last_updated_at), desc(Story.confidence_score))
            .offset(offset)
            .limit(limit)
        )
        
        result_stories = await session.execute(stmt_stories)
        stories = result_stories.scalars().all()
        
        formatted_stories = []
        for story in stories:
            stmt_pubs = (
                select(Publication)
                .options(selectinload(Publication.channel))
                .join(Channel)
                .where(
                    Publication.story_id == story.id,
                    Publication.channel_id.in_(user_channel_ids)
                )
                .order_by(desc(Publication.views))
                .limit(5) # Беремо більше джерел для деталей
            )
            res_pubs = await session.execute(stmt_pubs)
            pubs = res_pubs.scalars().all()
            
            sources = [{"name": p.channel.title, "url": p.url} for p in pubs if p.channel]
            primary_url = sources[0]["url"] if sources else None
            
            formatted_stories.append({
                "uid": f"story_{story.id}",
                "id": story.id,
                "type": "story",
                "title": clean_markdown(story.title),
                "summary": story.summary,
                "category": story.category or "📰 Події",
                "score": story.confidence_score,
                "sources": sources,
                "url": primary_url,
                "publications_count": len(pubs),
                "timestamp": story.last_updated_at
            })

        # 3. Отримуємо "Інші новини" (Briefs)
        story_ids = [s.id for s in stories]
        
        stmt_briefs = (
            select(Publication)
            .options(selectinload(Publication.channel))
            .join(Channel)
            .where(
                Publication.channel_id.in_(user_channel_ids),
                Publication.published_at >= time_threshold,
                (Publication.story_id.notin_(story_ids)) | (Publication.story_id.is_(None))
            )
        )

        if pinned_categories:
            if group_by == "category":
                stmt_briefs = stmt_briefs.where(Publication.category.in_(pinned_categories))
            elif group_by == "channel":
                stmt_briefs = stmt_briefs.where(Channel.title.in_(pinned_categories))

        stmt_briefs = (
            stmt_briefs.order_by(desc(Publication.published_at))
            .offset(offset)
            .limit(limit)
        )
        
        res_briefs = await session.execute(stmt_briefs)
        briefs = res_briefs.scalars().all()
        
        formatted_briefs = []
        for b in briefs:
            clean_text = clean_markdown(b.content)
            # Створюємо короткий заголовок з тексту для уніфікації списку
            title_words = clean_text.split()
            title = " ".join(title_words[:8]) + ("..." if len(title_words) > 8 else "")
            
            formatted_briefs.append({
                "uid": f"brief_{b.id}",
                "id": b.id,
                "type": "brief",
                "title": title,
                "summary": clean_text,
                "channel": b.channel.title if b.channel else "Unknown",
                "category": b.category or "📰 Події",
                "sources": [{"name": b.channel.title, "url": b.url}] if b.channel else [],
                "url": b.url,
                "time": b.published_at,
                "timestamp": b.published_at
            })

        # 4. Логіка сортування та групування
        if group_by == "time":
            all_items = []
            for s in formatted_stories:
                all_items.append({"type": "story", "data": s, "timestamp": s["timestamp"]})
            for b in formatted_briefs:
                all_items.append({"type": "brief", "data": b, "timestamp": b["timestamp"]})
            
            all_items.sort(key=lambda x: x["timestamp"], reverse=True)
            
            for item in all_items:
                # В режимі часу конвертуємо в ISO для фронтенда
                iso_time = item["timestamp"].replace(tzinfo=None).isoformat() + "Z"
                item["time"] = iso_time
                item["data"]["time"] = iso_time
                # Вичищаємо тимчасові поля
                if "timestamp" in item: del item["timestamp"]
                if "timestamp" in item["data"]: del item["data"]["timestamp"]

            return {
                "items": all_items,
                "has_more": len(formatted_stories) == limit or len(formatted_briefs) == limit,
                "stats": {"total": len(all_items), "mode": "time"}
            }

        elif group_by == "channel":
            # Новий режим: Групування за каналами
            channel_groups = {}
            for s in formatted_stories:
                # Беремо перший канал як основний для сюжету
                source = s["sources"][0]["name"] if s["sources"] else "📰 Інше"
                if source not in channel_groups: channel_groups[source] = []
                channel_groups[source].append({"type": "story", "data": s, "timestamp": s["timestamp"]})
            
            for b in formatted_briefs:
                source = b["channel"]
                if source not in channel_groups: channel_groups[source] = []
                channel_groups[source].append({"type": "brief", "data": b, "timestamp": b["timestamp"]})
            
            final_channels = {}
            for source, items in channel_groups.items():
                items.sort(key=lambda x: x["timestamp"], reverse=True)
                for item in items:
                    iso_time = item["timestamp"].replace(tzinfo=None).isoformat() + "Z"
                    item["time"] = iso_time
                    item["data"]["time"] = iso_time
                    if "timestamp" in item: del item["timestamp"]
                    if "timestamp" in item["data"]: del item["data"]["timestamp"]
                
                final_channels[source] = {
                    "items": items[:2], # Ліміт 2 для головної
                    "has_more": len(items) > 2,
                    "total_count": len(items)
                }
            
            # Сортування каналів за алфавітом або часом останнього посту
            sorted_channels = dict(sorted(final_channels.items()))

            return {
                "channels": sorted_channels,
                "has_more": len(formatted_stories) == limit or len(formatted_briefs) == limit,
                "stats": {"total_channels": len(sorted_channels), "mode": "channel"}
            }

        else: # group_by == "category"
            merged_categories = {}
            for s in formatted_stories:
                cat = s.get("category") or "📰 Інше"
                if cat not in merged_categories: merged_categories[cat] = []
                merged_categories[cat].append({"type": "story", "data": s, "timestamp": s["timestamp"]})
            
            for b in formatted_briefs:
                cat = b.get("category") or "📰 Інше"
                if cat not in merged_categories: merged_categories[cat] = []
                merged_categories[cat].append({"type": "brief", "data": b, "timestamp": b["timestamp"]})

            final_categories = {}
            for cat, items in merged_categories.items():
                items.sort(key=lambda x: x["timestamp"], reverse=True)
                for item in items:
                    iso_time = item["timestamp"].replace(tzinfo=None).isoformat() + "Z"
                    item["time"] = iso_time
                    item["data"]["time"] = iso_time
                    if "timestamp" in item: del item["timestamp"]
                    if "timestamp" in item["data"]: del item["data"]["timestamp"]
                
                final_categories[cat] = {
                    "items": items[:2],
                    "has_more": len(items) > 2,
                    "total_count": len(items)
                }

            # Сортування: pinned спочатку, потім Авторські, потім решта
            def sort_key(cat):
                if pinned_categories and cat in pinned_categories: return (0, cat)
                if "автор" in cat.lower(): return (1, cat)
                return (2, cat)
            
            sorted_categories = dict(sorted(final_categories.items(), key=lambda x: sort_key(x[0])))

            return {
                "categories": sorted_categories,
                "has_more": len(formatted_stories) == limit or len(formatted_briefs) == limit,
                "stats": {
                    "total_stories": len(formatted_stories), 
                    "total_briefs": len(formatted_briefs), 
                    "mode": "category"
                }
            }

async def get_user_digest(user_id: int) -> str | None:
    """
    Генерує текстовий дайджест для бота (Fallback).
    """
    try:
        # Отримуємо дані за останні 24 години
        data = await get_user_digest_data(user_id, hours=24)
        
        if "error" in data:
            return None
            
        # Prepare context for AI (rebuilding top_stories and other_news from categories)
        ai_context = {
            "top_stories": [],
            "other_news": []
        }
        
        seen_uids = set()
        if "categories" in data:
            for cat_data in data["categories"].values():
                for item in cat_data["items"]:
                    if item["data"]["uid"] in seen_uids:
                        continue
                    seen_uids.add(item["data"]["uid"])
                    
                    if item["type"] == "story":
                        ai_context["top_stories"].append(item["data"])
                    else:
                        # For briefs, remap 'summary' to 'text' as expected by old AI service logic
                        brief_data = item["data"].copy()
                        brief_data["text"] = brief_data.get("summary", "")
                        ai_context["other_news"].append(brief_data)
        
        if not ai_context["top_stories"] and not ai_context["other_news"]:
            return "📭 У ваших каналах поки тихо. Новин для дайджесту немає."

        # Генеруємо текст через AI
        logger.info(f"Generating text digest for user {user_id}...")
        return await generate_daily_digest(ai_context)

    except Exception as e:
        logger.error(f"Error generating digest for user {user_id}: {e}")
        return "❌ Вибачте, сталася помилка при генерації дайджесту."
