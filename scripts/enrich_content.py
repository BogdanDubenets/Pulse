
import asyncio
import json
from database.connection import AsyncSessionLocal
from database.models import Publication, Story, Channel
from sqlalchemy import select, func, update
from services.ai_service import model, CATEGORY_MAP, CATEGORY_NAMES_FOR_AI
from loguru import logger

async def categorize_everything():
    async with AsyncSessionLocal() as session:
        # 1. Update stories (rename placeholder titles)
        stmt_stories = select(Story).where(Story.title.in_(["Нова історія", None]))
        stories = (await session.execute(stmt_stories)).scalars().all()
        print(f"Enriching {len(stories)} stories...")
        
        for s in stories:
            stmt_p = select(Publication.content).where(Publication.story_id == s.id).limit(3)
            p_texts = (await session.execute(stmt_p)).scalars().all()
            if not p_texts: continue
            
            prompt = f"Придумай заголовок, саммарі та категорію (з переліку: {', '.join(CATEGORY_NAMES_FOR_AI)}) для цієї новини:\n\n" + "\n".join(p_texts)
            try:
                response = await model.generate_content_async(prompt, generation_config={"response_mime_type": "application/json"})
                data = json.loads(response.text)
                s.title = data.get("title", s.title)
                s.summary = data.get("summary", s.summary)
                raw_cat = data.get("category", "Події")
                s.category = CATEGORY_MAP.get(raw_cat, f"📰 {raw_cat}")
                print(f"Updated Story {s.id}: {s.title}")
            except Exception as e: print(f"Error story {s.id}: {e}")

        # 2. Categorize ALL publications without category
        stmt_pubs = select(Publication).where(Publication.category == None)
        pubs = (await session.execute(stmt_pubs)).scalars().all()
        print(f"Categorizing {len(pubs)} publications...")

        # Batch processing (10 at a time)
        for i in range(0, len(pubs), 10):
            batch = pubs[i:i+10]
            batch_data = [{"id": p.id, "text": p.content[:300]} for p in batch]
            
            prompt = f"""Для кожної новини з масиву нижче вибери РІВНО ОДНУ категорію з переліку: {', '.join(CATEGORY_NAMES_FOR_AI)}.
Відповідай у форматі JSON масиву об'єктів {{ "id": id, "category": "..." }}.

Новини:
{json.dumps(batch_data, ensure_ascii=False)}
"""
            try:
                response = await model.generate_content_async(prompt, generation_config={"response_mime_type": "application/json"})
                results = json.loads(response.text)
                for res in results:
                    p_id = res.get("id")
                    cat_name = res.get("category")
                    full_cat = CATEGORY_MAP.get(cat_name, f"📰 {cat_name}")
                    await session.execute(update(Publication).where(Publication.id == p_id).values(category=full_cat))
                print(f"Processed batch {i//10 + 1}/{(len(pubs)//10)+1}")
            except Exception as e:
                print(f"Error in batch {i}: {e}")
            
            # Commit every few batches to save progress
            if i % 50 == 0:
                await session.commit()
                print("Checkpoint saved")

        await session.commit()
        print("Categorization complete")

if __name__ == "__main__":
    asyncio.run(categorize_everything())
