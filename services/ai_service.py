"""
Pulse AI Service — класифікація каналів та генерація дайджестів через Google Gemini.
Використовує новий SDK google-genai (замість deprecated google-generativeai).
"""

from google import genai
from google.genai import types
from config.settings import config
from bot.categories import CATEGORY_NAMES_FOR_AI, CATEGORY_MAP
from loguru import logger


# Ініціалізація клієнта Gemini з підтримкою v1beta (для text-embedding-004)
client = genai.Client(api_key=config.GEMINI_API_KEY)

from database.connection import AsyncSessionLocal
from database.models import Category
from sqlalchemy import select

# Модель для генерації тексту
MODEL_ID = "gemini-2.0-flash"

# Промпт для класифікації каналу
CLASSIFY_PROMPT = """Ти — AI-класифікатор українських Telegram-каналів.

Проаналізуй інформацію про канал і визнач його категорію.

Дозволені категорії (обери РІВНО ОДНУ):
{categories}

Інформація про канал:
- Назва: {title}
- Юзернейм: @{username}
- Зразок контенту: {sample_text}

Відповідай ЛИШЕ назвою однієї категорії з дозволеного списку, без пояснень та зайвих символів.
Якщо канал регіональний — обирай відповідну область.
Якщо не можеш визначити — відповідай "Події".
"""


async def get_existing_categories() -> list[str]:
    """Отримує список назв категорій з БД."""
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(Category.name).where(Category.is_visible == True)
            res = await session.execute(stmt)
            return list(res.scalars().all())
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return CATEGORY_NAMES_FOR_AI

async def classify_channel(title: str, username: str | None, sample_text: str | None) -> str:
    """
    Визначає категорію каналу через Gemini Flash.
    """
    try:
        existing_cats = await get_existing_categories()
        prompt = CLASSIFY_PROMPT.format(
            categories="\n".join(f"- {c}" for c in existing_cats),
            title=title or "невідомо",
            username=username or "відсутній",
            sample_text=(sample_text or "текст відсутній")[:500]
        )
        
        logger.debug(f"Classifying channel: {title}")
        
        response = await client.aio.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=50,
            )
        )
        
        result = response.text.strip()
        logger.info(f"Gemini classified '{title}' as: {result}")
        
        # Шукаємо найкращий збіг у дозволених категоріях
        if result in CATEGORY_MAP:
            return CATEGORY_MAP[result]
        
        # Пошук часткового збігу
        for name, full_cat in CATEGORY_MAP.items():
            if name.lower() in result.lower() or result.lower() in name.lower():
                logger.debug(f"Partial match: '{result}' → '{full_cat}'")
                return full_cat
        
        logger.warning(f"Unknown category from Gemini: '{result}', falling back to '📰 Події'")
        return "📰 Події"
        
    except Exception as e:
        logger.error(f"Gemini classification error: {e}")
        return "📰 Події"


async def get_text_embedding(text: str) -> list[float] | None:
    """
    Генерує векторне представлення тексту (embedding) через Gemini.
    Model: gemini-embedding-001
    Output dimension: 768
    """
    try:
        if not text:
            return None
            
        truncated_text = text[:8000]
        
        result = await client.aio.models.embed_content(
            model="gemini-embedding-001",
            contents=truncated_text,
            config=types.EmbedContentConfig(
                task_type="CLUSTERING",
                output_dimensionality=768,
            ),
        )
        
        if result.embeddings and len(result.embeddings) > 0:
            return list(result.embeddings[0].values)
        return None
        
    except Exception as e:
        logger.error(f"Gemini embedding error: {e}")
        return None


async def generate_story_info(text: str) -> dict:
    """
    Генерує заголовок, короткий опис та категорію для нової історії.
    """
    prompt = f"""Проаналізуй текст новини та створи для неї метадані.
Це індивідуальна новина з Telegram-каналу.

Текст:
{text[:2000]}

Необхідні дані:
1. Заголовок (до 10 слів, інформативний, без клікбейту, суть події)
2. Саммарі (до 2 речень, стисло)
3. Категорія (обери ОДНУ з: Політика, Війна, Суспільство, Економіка, Світ, Технології, Спорт, Кримінал, Культура)

Відповідай у форматі JSON:
{{
  "title": "...",
  "summary": "...",
  "category": "..."
}}
"""
    try:
        response = await client.aio.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        import json
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Gemini story generation error: {e}")
        return {
            "title": "Нова історія",
            "summary": "Автоматично створена історія",
            "category": "Події"
        }


async def generate_digest(news_items: list[dict]) -> str:
    """
    Генерує дайджест на основі списку новин.
    """
    if not news_items:
        return "Немає новин для дайджесту."

    formatted_news = ""
    for item in news_items:
        formatted_news += f"Канал: {item['channel']}\nТекст: {item['text'][:500]}...\n\n"

    prompt = f"""Ти — професійний редактор новин. Твоє завдання — створити лаконічний дайджест на основі останніх новин з підписаних каналів користувача.

Вхідні дані (по одній новині з каналу):
{formatted_news}

Вимоги до дайджесту:
1. Згрупуй новини за темами (наприклад, 🌍 Світ, 🇺🇦 Україна, 💵 Економіка, 🚀 Технології), якщо це можливо.
2. Для кожної новини напиши:
   - Короткий заголовок/суть (1 речення, жирним).
   - Джерело (назва каналу курсивом).
3. Використовуй емодзі для візуального структурування.
4. Стиль: інформативний, об'єктивний, без зайвих слів.
5. На початку додай заголовок "📰 Ваш персональний дайджест".
6. В кінці додай заклик: "Детальніше читайте в каналах."

Для джерела ОБОВ'ЯЗКОВО використовуй формат Markdown: [Назва каналу](url).
Якщо url порожній — просто пиши назву курсивом.
"""

    try:
        response = await client.aio.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
            )
        )
        logger.info(f"Gemini usage: {response.usage_metadata}")
        return response.text
    except Exception as e:
        logger.error(f"AI Generation Error: {e}")
        return "Вибачте, не вдалося згенерувати дайджест через помилку AI."


async def generate_daily_digest(context: dict) -> str:
    """
    Генерує розширений дайджест дня.
    context: {
        "top_stories": [{"title": str, "summary": str, "sources": [Source]}],
        "other_news": [{"channel": str, "text": str, "url": str}]
    }
    """
    if not context.get("top_stories") and not context.get("other_news"):
        return "Сьогодні було тихо. Новин немає."

    # Формуємо контекст для промпта
    stories_text = ""
    for i, story in enumerate(context.get("top_stories", []), 1):
        # Витягуємо назви з об'єктів Source
        source_names = [s['name'] for s in story.get('sources', []) if isinstance(s, dict) and 'name' in s]
        if not source_names:
            source_names = [s for s in story.get('sources', []) if isinstance(s, str)]
            
        sources = ", ".join(source_names[:3])
        stories_text += f"{i}. {story['title']}\n   Суть: {story['summary']}\n   Джерела: {sources}\n\n"

    other_text = ""
    for item in context.get("other_news", []):
        text = item.get('text') or item.get('summary', '')
        other_text += f"- {item['channel']}: {text[:200]}... ({item.get('url', '')})\n"

    prompt = f"""Ти — ведучий новин Pulse. Твоє завдання — створити вечірній/ранковий дайджест головних подій.

Ось головні сюжети дня (вже згруповані):
{stories_text}

Ось інші окремі новини:
{other_text}

Створи структурований звіт у форматі Markdown:
1. **🔥 ГОЛОВНІ СЮЖЕТИ** (Top Stories)
   - Опиши кожен сюжет одним абзацом.
   - Виділи жирним найголовніше.
   - Вкажи джерела курсивом в дужках (наприклад: *Forbes, BBC*).
   
2. **📰 КОРОТКО ПРО ІНШЕ** (Briefs)
   - Список (bullet points) з 3-5 найцікавіших інших новин.
   - Тільки суть, 1 речення.
   - Вкажи канал-джерело.

Стиль: 
- Преміальний, діловий, але живий українська мова.
- Використовуй емодзі помірно.
- Не пиши "Ось ваш дайджест", починай одразу з заголовка "🔥 ГОЛОВНІ СЮЖЕТИ".

Максимальна довжина: 3000 символів (щоб вмістилось в одне повідомлення Telegram).
"""

    try:
        response = await client.aio.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
            )
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini daily digest error: {e}")
        return "Не вдалося згенерувати дайджест."
