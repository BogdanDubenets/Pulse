# Дорожня карта розвитку Telegram News Bot

## Огляд проекту

**Концепція:** Telegram-бот який автоматично збирає, резюмує та агрегує новини з публічних каналів на які підписаний користувач.

**Унікальна цінність:**
- Автоматичний моніторинг обраних каналів
- Дедуплікація новин (одна новина з багатьох джерел)
- Персоналізовані дайджести
- Найпростіше додавання каналів (через forward)
- Система верифікації новин (підтвердження з кількох джерел)
- Аналітика поширення новин

---

## Архітектура системи

### Технічний стек
- **Backend:** Python 3.11+
- **Bot Framework:** aiogram 3.x
- **Моніторинг каналів:** Telethon (Telegram Client API)
- **База даних:** PostgreSQL
- **Черга завдань:** Celery + Redis
- **LLM:** Claude Haiku/Sonnet (Anthropic API)
- **Векторизація:** OpenAI Embeddings або Cohere
- **TTS (майбутнє):** ElevenLabs або Google Cloud TTS
- **Хостинг:** Railway, Fly.io або DigitalOcean

### Структура БД

#### Основні таблиці

**STORY (Новина - центральна сутність)**
```sql
CREATE TABLE stories (
    id SERIAL PRIMARY KEY,
    title TEXT,
    summary TEXT,
    category TEXT,
    first_seen_at TIMESTAMP,
    last_updated_at TIMESTAMP,
    confidence_score FLOAT,  -- 0.0 to 1.0
    status TEXT,  -- pending, verified, trending, archived
    embedding_vector VECTOR(1536)
);
```

**STORY_PUBLICATION (Кожна публікація новини)**
```sql
CREATE TABLE story_publications (
    id SERIAL PRIMARY KEY,
    story_id INTEGER REFERENCES stories(id),
    channel_id INTEGER REFERENCES channels(id),
    post_id BIGINT,  -- Telegram message ID
    post_url TEXT,
    original_text TEXT,
    published_at TIMESTAMP,
    reactions_count INTEGER,
    views_count INTEGER,
    comments_count INTEGER,
    word_count INTEGER,
    has_media BOOLEAN,
    media_urls TEXT[],
    embedding_vector VECTOR(1536)
);
```

**CHANNEL (Канали)**
```sql
CREATE TABLE channels (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    username TEXT,
    title TEXT,
    description TEXT,
    subscribers_count INTEGER,
    category TEXT,
    avg_post_frequency FLOAT,
    credibility_score FLOAT,
    partnership_status TEXT,  -- none, partner, premium, featured
    is_public BOOLEAN,
    added_at TIMESTAMP
);
```

**USER_SUBSCRIPTION (Підписки користувачів)**
```sql
CREATE TABLE user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    channel_id INTEGER REFERENCES channels(id),
    added_at TIMESTAMP,
    added_method TEXT,  -- catalog, forward, search, link
    is_active BOOLEAN DEFAULT true
);
```

**STORY_ANALYTICS (Агрегована аналітика)**
```sql
CREATE TABLE story_analytics (
    story_id INTEGER PRIMARY KEY REFERENCES stories(id),
    total_publications INTEGER,
    unique_channels INTEGER,
    first_channel_id INTEGER REFERENCES channels(id),
    first_published_at TIMESTAMP,
    peak_publication_time TIMESTAMP,
    total_reach BIGINT,  -- сума підписників всіх каналів
    avg_engagement_rate FLOAT,
    spread_velocity FLOAT,  -- publications per hour
    geographic_spread TEXT[]
);
```

### Алгоритм обробки новин

**Pipeline:**
```
1. ЗБІР ПОСТІВ
   └─ Telethon моніторить канали кожні 5-10 хв
   └─ Зберігає нові пости в story_publications

2. ВЕКТОРИЗАЦІЯ
   └─ Генерує embedding для кожного поста
   └─ Використовує OpenAI text-embedding-3-small

3. КЛАСТЕРИЗАЦІЯ
   └─ Cosine similarity > 0.85 → одна новина
   └─ Створює або оновлює запис в stories
   └─ Пов'язує publications з story

4. ВЕРИФІКАЦІЯ
   └─ 1 джерело: status = 'pending'
   └─ 2+ джерела: status = 'verified'
   └─ 5+ джерел: status = 'trending'
   └─ Розраховує confidence_score

5. ВИЗНАЧЕННЯ ПЕРШОДЖЕРЕЛА
   └─ Сортування по published_at
   └─ Перевірка на офіційні джерела
   └─ Аналіз деталізації (word_count)

6. ГЕНЕРАЦІЯ САММАРІ
   └─ LLM отримує всі публікації кластеру
   └─ Створює короткий зміст (150-300 слів)
   └─ Зберігає в stories.summary

7. АНАЛІЗ ПОШИРЕННЯ
   └─ Розраховує метрики в story_analytics
   └─ Швидкість, reach, engagement

8. ПЕРСОНАЛІЗАЦІЯ
   └─ Для кожного користувача фільтрує по його каналах
   └─ Генерує персональний дайджест
```

### Система confidence score

```python
def calculate_confidence(story):
    score = 0.0
    
    # Базовий score від кількості джерел
    if story.sources_count == 1:
        score = 0.3
    elif story.sources_count == 2:
        score = 0.6
    elif story.sources_count >= 3:
        score = 0.9
    
    # Бонус за credibility джерел
    for source in story.sources:
        if source.channel.credibility_score > 0.8:
            score += 0.05
    
    # Бонус за швидкість підтвердження
    if story.confirmation_time < 30_minutes:
        score += 0.1
    
    # Штраф за затримку
    if story.age > 24_hours and story.sources_count == 1:
        score -= 0.2
    
    return min(score, 1.0)
```

### Статуси новин

- **pending:** 1 джерело, чекаємо підтвердження (не показуємо користувачу)
- **verified:** 2+ джерела, можна включати в дайджест
- **trending:** 5+ джерел за короткий час, високий engagement
- **archived:** старіше 48 годин, більше не оновлюється

---

## ФАЗА 1: MVP - Bot для користувачів (Місяці 1-3)

### Мета
Довести що продукт працює і потрібен. Отримати перших 500 активних користувачів.

### Функціональність

#### 1.1 Базовий бот

**Команди:**
- `/start` - Вітання, реєстрація, onboarding
- `/help` - Довідка
- `/add` - Додати канал через посилання
- `/channels` - Список моїх каналів
- `/summary` - Отримати дайджест зараз
- `/settings` - Налаштування (час дайджесту, категорії)

**Onboarding flow:**
```
1. /start → Вітання
   "Привіт! Я допоможу не пропустити важливі новини 
    з твоїх улюблених Telegram каналів."

2. Пропозиція додати канали:
   "Обери спосіб додавання:
    📚 Каталог популярних каналів
    🔗 Додати посиланням
    📤 Поділитися постом з каналу"

3. Якщо обрано каталог:
   "Обери категорії (можна кілька):
    📰 Новини
    💼 Бізнес
    💻 Технології
    ⚖️ Політика"
   
4. Показати топ-15 каналів в обраних категоріях
   Галочки для вибору

5. Підтвердження:
   "Чудово! Моніторинг розпочато.
    Перший дайджест отримаєш сьогодні о 20:00"
```

#### 1.2 Каталог каналів

**Стартовий каталог: 50-100 найпопулярніших українських каналів**

**Категорії:**
- 📰 Загальні новини (20 каналів)
  - Українська правда, НВ, Forbes Ukraine, Економічна правда, LB.ua, Цензор.нет, TCH, Громадське ТБ, Суспільне, Babel
  
- 💼 Бізнес/Економіка (15 каналів)
  - Мінфін, MC.today, AIN.UA, Delo.ua, Бізнес Цензор, Ліга Бізнес, Invest Рада
  
- 💻 Технології (10 каналів)
  - DOU, tech.mc, dev.ua, Watcher, IT Arena, Ain Tech, Projector
  
- ⚖️ Політика/Суспільство (15 каналів)
  - Зе!команда, Слуга народу, ЄС, Радіо Свобода, Схеми, Slidstvo.Info
  
- 🎨 Культура/Лайфстайл (10 каналів)
  - The Village Україна, Vogue UA, GQ Ukraine, Elle Ukraine

**Критерії відбору:**
- 10K+ підписників
- Регулярні публікації (мін. 1 пост/день)
- Публічний канал з @username
- Перевірена репутація

**UI каталогу:**
```
📚 КАТАЛОГ КАНАЛІВ

📰 Загальні новини (20)
[Показати всі →]

Топ-5:
☐ Українська правда (1.2M підписників)
☐ НВ (890K підписників)
☐ Forbes Ukraine (450K підписників)
...

💼 Бізнес/Економіка (15)
[Показати всі →]
```

#### 1.3 Додавання через Forward/Share ⭐

**Як працює:**
```python
@bot.message_handler(content_types=['forward'])
async def handle_forward(message):
    # Перевіряємо чи це forward з каналу
    if not message.forward_from_chat:
        return await message.reply("Це не канал")
    
    if message.forward_from_chat.type != 'channel':
        return await message.reply("Це не канал, а група або бот")
    
    channel_id = message.forward_from_chat.id
    channel_title = message.forward_from_chat.title
    channel_username = message.forward_from_chat.username
    
    # Перевіряємо чи канал вже доданий
    if channel_already_added(user_id, channel_id):
        return await show_channel_already_added(message, channel_title)
    
    # Перевіряємо чи канал публічний
    is_public = channel_username is not None
    
    if is_public:
        # Отримуємо додаткову інфо через Telethon
        channel_info = await get_channel_info(channel_username)
        
        # Показуємо діалог підтвердження
        await show_add_confirmation(message, channel_info)
    else:
        # Приватний канал
        await show_private_channel_message(message, channel_title)
```

**UI для підтвердження:**
```
✨ Новий канал знайдено!

📢 Forbes Ukraine
👥 450K підписників
📊 ~8 постів/день
🏷️ #економіка #бізнес

Додати до моніторингу?

Ти зараз моніториш: 5/10 каналів (Free план)

[✅ Додати] [❌ Ні, дякую]
```

**Batch add (якщо форварднуто 3+ постів):**
```
✨ Знайдено 5 нових каналів!

✅ Forbes Ukraine
✅ Економічна правда
✅ MC.today
✅ НВ Бізнес
✅ Мінфін

[Додати всі (5)] [Вибрати вручну]
```

**Для приватних каналів:**
```
⚠️ Це приватний канал

Я можу зберегти його в списку, але 
не зможу автоматично збирати пости.

Ти можеш:
✅ Періодично форвардити цікаві пости
✅ Перейти на Pro план з підтримкою 
   приватних каналів (скоро)

[Додати з ручним forward] [Дізнатися про Pro]
```

#### 1.4 Моніторинг каналів

**Технічна реалізація через Telethon:**

```python
from telethon import TelegramClient
from telethon.tl.types import Channel

class ChannelMonitor:
    def __init__(self, api_id, api_hash):
        self.client = TelegramClient('monitor', api_id, api_hash)
        self.last_message_ids = {}  # {channel_id: last_msg_id}
    
    async def start(self):
        await self.client.start()
    
    async def monitor_channels(self, channel_list):
        """Перевіряє нові пости кожні 5 хвилин"""
        for channel_id in channel_list:
            try:
                new_posts = await self.get_new_posts(channel_id)
                if new_posts:
                    await self.process_posts(new_posts)
            except Exception as e:
                logger.error(f"Error monitoring {channel_id}: {e}")
    
    async def get_new_posts(self, channel_id):
        """Отримує тільки нові пости"""
        last_id = self.last_message_ids.get(channel_id, 0)
        
        messages = await self.client.get_messages(
            channel_id,
            min_id=last_id,
            limit=100
        )
        
        if messages:
            self.last_message_ids[channel_id] = messages[0].id
        
        return messages
```

**Обробка зібраних постів:**
```python
async def process_posts(posts):
    for post in posts:
        # Зберігаємо в БД
        publication = StoryPublication.create(
            channel_id=post.peer_id.channel_id,
            post_id=post.id,
            original_text=post.message,
            published_at=post.date,
            views_count=post.views,
            reactions_count=count_reactions(post)
        )
        
        # Генеруємо embedding
        embedding = await generate_embedding(post.message)
        publication.embedding_vector = embedding
        publication.save()
        
        # Запускаємо кластеризацію (async task)
        await cluster_publications.delay()
```

#### 1.5 Кластеризація та верифікація

**Алгоритм кластеризації:**
```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

async def cluster_new_publication(publication):
    """
    Знаходить до якої новини відноситься публікація
    або створює нову новину
    """
    
    # Отримуємо всі verified/pending новини за останні 24 год
    recent_stories = Story.objects.filter(
        status__in=['pending', 'verified', 'trending'],
        first_seen_at__gte=datetime.now() - timedelta(hours=24)
    )
    
    if not recent_stories:
        # Це перша публікація - створюємо нову новину
        return create_new_story(publication)
    
    # Порівнюємо embedding з існуючими новинами
    best_match = None
    best_similarity = 0.0
    
    for story in recent_stories:
        # Беремо середній embedding всіх публікацій новини
        story_embedding = np.mean([
            pub.embedding_vector 
            for pub in story.publications.all()
        ], axis=0)
        
        similarity = cosine_similarity(
            [publication.embedding_vector],
            [story_embedding]
        )[0][0]
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = story
    
    # Threshold для схожості
    if best_similarity > 0.85:
        # Це та ж новина - додаємо публікацію
        story.publications.add(publication)
        story.update_status()  # Перевіряємо чи треба змінити статус
        return story
    else:
        # Це нова окрема новина
        return create_new_story(publication)

def create_new_story(publication):
    story = Story.create(
        title=generate_title(publication.original_text),
        status='pending',
        confidence_score=0.3,
        first_seen_at=publication.published_at
    )
    story.publications.add(publication)
    return story
```

**Оновлення статусу новини:**
```python
def update_story_status(story):
    sources_count = story.publications.count()
    
    # Визначаємо новий статус
    if sources_count == 1:
        new_status = 'pending'
    elif sources_count == 2:
        new_status = 'verified'
    elif sources_count >= 5:
        # Перевіряємо швидкість поширення
        time_span = (
            story.publications.last().published_at - 
            story.publications.first().published_at
        )
        if time_span.total_seconds() < 3600:  # За годину 5+ джерел
            new_status = 'trending'
        else:
            new_status = 'verified'
    else:
        new_status = 'verified'
    
    # Оновлюємо
    story.status = new_status
    story.confidence_score = calculate_confidence(story)
    story.save()
    
    # Якщо статус змінився на verified - генеруємо саммарі
    if new_status == 'verified' and not story.summary:
        generate_summary.delay(story.id)
```

#### 1.6 Генерація дайджестів

**Коли генеруємо:**
- Щодня о 20:00 за замовчуванням (користувач може змінити)
- За запитом користувача (команда /summary)
- Real-time для trending новин (опційно)

**Алгоритм:**
```python
async def generate_user_digest(user_id, date=None):
    if date is None:
        date = datetime.now().date()
    
    # Отримуємо канали користувача
    user_channels = UserSubscription.objects.filter(
        user_id=user_id,
        is_active=True
    ).values_list('channel_id', flat=True)
    
    # Отримуємо всі verified новини за день
    stories = Story.objects.filter(
        status__in=['verified', 'trending'],
        first_seen_at__date=date
    ).order_by('-confidence_score', 'first_seen_at')
    
    digest_items = []
    
    for story in stories:
        # Фільтруємо публікації по каналах користувача
        user_publications = story.publications.filter(
            channel_id__in=user_channels
        ).order_by('published_at')
        
        if not user_publications.exists():
            continue  # Новини немає в каналах користувача
        
        # Збираємо інфо для дайджесту
        item = {
            'story': story,
            'summary': story.summary,
            'user_sources': user_publications,
            'total_sources': story.publications.count(),
            'first_source': user_publications.first(),
            'category': story.category,
            'is_trending': story.status == 'trending'
        }
        digest_items.append(item)
    
    # Групуємо по категоріях
    categorized = group_by_category(digest_items)
    
    # Форматуємо для відправки
    return format_digest(categorized)
```

**Формат дайджесту:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📰 ДАЙДЖЕСТ за 15 лютого 2026

🔥 TRENDING (2)

🔴 Нова економічна реформа

Уряд оголосив пакет реформ який вплине 
на малий бізнес. Основні зміни: спрощення 
реєстрації, зниження податків для стартапів, 
цифровізація послуг.

📌 У твоїх каналах (3 з 7):
• Мінфін - 11:23 ⚡ першоджерело
• Forbes UA - 12:10 (детальний аналіз)
• Економічна правда - 11:45

[Детальніше] [Оригінали]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔵 Запуск нового стартапу в AI

Ukrainian startup MonoAI залучив $2M...

📌 У твоїх каналах (2 з 4):
• AIN.UA - 14:30
• tech.mc - 15:10

[Детальніше]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💼 БІЗНЕС (5 новин)

[Показати всі →]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💻 ТЕХНОЛОГІЇ (3 новини)

[Показати всі →]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Цей дайджест згенеровано з 15 каналів
Наступний: завтра о 20:00

[Налаштування] [Додати канали]
```

**Детальний вигляд новини:**
```
🔴 Нова економічна реформа

📝 ПОВНИЙ ЗМІСТ

[Розширене резюме 300-500 слів з основними
 пунктами, цитатами, контекстом]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 ПОКРИТТЯ (7 джерел)

⭐⭐⭐ Найдетальніше:
📢 Forbes Ukraine - 12:10
   487 слів, інфографіка
   [Читати повністю →]

⭐⭐ Середня деталізація:
📢 Економічна правда - 11:45
   312 слів
📢 MC.today - 13:20
   245 слів

⭐ Коротко:
📢 Мінфін - 11:23 ⚡ першоджерело
   Офіційна заява, 89 слів
📢 НВ Бізнес - 14:20
📢 AIN.UA - 15:33
📢 delo.ua - 16:05

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 АНАЛІЗ ПОШИРЕННЯ

⏱ Timeline:
11:23 - Мінфін (офіційна заява)
11:45 - Економічна правда (+22 хв)
12:10 - Forbes UA (+47 хв)
13:20 - MC.today (+1 год 57 хв)
...

🚀 Швидкість: 7 каналів за 5 годин
📍 Reach: 3.2M підписників
💬 Engagement: 8,234 reactions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 У твоїх каналах: 3 з 7
Канали які також покрили:
• НВ Бізнес
• AIN.UA
• delo.ua

[Додати ці канали?]
```

#### 1.7 Персоналізація

**Налаштування користувача:**
```
⚙️ НАЛАШТУВАННЯ

🕐 Час дайджесту:
   Поточний: 20:00
   [Змінити]

📅 Частота:
   ☑ Щодня
   ☐ Тільки будні
   ☐ Вибрані дні
   [Налаштувати]

📂 Категорії:
   Які новини включати:
   ☑ Всі
   ☐ Тільки trending
   ☐ Вибрані категорії:
      ☑ Новини
      ☑ Бізнес
      ☐ Технології
      ☐ Політика

📊 Обсяг дайджесту:
   ◉ Короткий (топ-10 новин)
   ○ Повний (всі новини)
   ○ Custom

🔕 Не турбувати:
   З 23:00 до 08:00
   [Налаштувати]
```

### MVP Scope - Що робимо

**✅ Включено в MVP:**
- Базовий бот з командами
- Каталог 50-100 топ-каналів
- Додавання через forward/share
- Додавання через посилання
- Моніторинг публічних каналів
- Векторизація та кластеризація
- Система верифікації (2+ джерела)
- Щоденні текстові дайджести
- Базова персоналізація
- Attribution (показ джерел)
- Базова БД з аналітикою

**❌ НЕ включено в MVP:**
- Подкасти (audio digest)
- Складна аналітика поширення
- Dashboard для каналів
- Партнерська програма
- Приватні канали
- Групи
- API
- Свій медіа-канал

### Технічні вимоги MVP

**Infrastructure:**
- PostgreSQL 14+ з pgvector extension
- Redis для черг та кешування
- Celery workers (2-3 workers)
- Server: 2 CPU, 4GB RAM мінімум

**Rate limits:**
- Telethon: ~20 req/sec per account
- LLM API: залежить від провайдера
- БД: оптимізація індексів для швидких запитів

**Витрати на користувача (орієнтовно):**
```
Користувач з 10 каналами:

LLM витрати (Claude Haiku):
- Input: ~30K токенів/день × $0.25/1M = $0.0075
- Output: ~2K токенів/день × $1.25/1M = $0.0025
- Разом: ~$0.01/день = $0.30/міс

Embeddings (OpenAI):
- ~50 постів/день × 500 токенів = 25K токенів
- $0.13/1M токенів = $0.003/день = $0.10/міс

Infrastructure: ~$0.10/користувача/міс

Загальні витрати: ~$0.50/користувача/міс
```

### KPI для завершення Фази 1

**Метрики успіху:**
- ✅ 500+ активних користувачів
- ✅ 70%+ retention за тиждень
- ✅ 50%+ retention за місяць
- ✅ Avg 5+ каналів на користувача
- ✅ 80%+ користувачів відкривають дайджест
- ✅ <5% error rate в кластеризації
- ✅ <30 хв затримка від публікації до дайджесту

**Feedback metrics:**
- Середній rating дайджестів: 4+/5
- NPS (Net Promoter Score): 30+
- Позитивні відгуки про UX

**Технічні метрики:**
- 99% uptime
- <5 сек response time боту
- Коректна кластеризація 90%+ випадків

### Timeline Фази 1

**Тиждень 1-2: Setup**
- Налаштування інфраструктури
- PostgreSQL + pgvector
- Базова архітектура БД
- Setup Telethon

**Тиждень 3-4: Моніторинг**
- Імплементація channel monitor
- Збір постів з каналів
- Збереження в БД

**Тиждень 5-6: Кластеризація**
- Векторизація постів
- Алгоритм кластеризації
- Система верифікації

**Тиждень 7-8: Бот UX**
- Базові команди
- Onboarding flow
- Каталог каналів
- Forward handler

**Тиждень 9-10: Дайджести**
- Генерація саммарі через LLM
- Форматування дайджестів
- Персоналізація по користувачах

**Тиждень 11-12: Testing & Launch**
- Beta testing з 20-50 користувачами
- Bug fixes
- Оптимізація
- Публічний launch

---

## ФАЗА 2: Аналітична платформа (Місяці 4-6)

### Мета
Створити цінність для каналів. Підготувати базу для партнерств.

### Функціональність

#### 2.1 Повна аналітика поширення

**Що відстежуємо для кожної новини:**

**Timeline розповсюдження:**
```sql
-- Приклад даних
Story: "Нова економічна реформа"

Publications timeline:
11:23:00 - @minfin_ua (офіційна заява)
11:45:30 - @economichna_p (+22 хв 30 сек)
12:10:15 - @forbes_ua (+47 хв 15 сек)
12:35:00 - @nv_business (+1 год 12 хв)
13:20:45 - @mc_today (+1 год 57 хв)
14:30:00 - @ain_ua (+3 год 7 хв)
16:05:30 - @delo_ua (+4 год 42 хв)
```

**Метрики швидкості:**
- Час до першого підтвердження (22 хв 30 сек)
- Час до 5 джерел (3 год 7 хв)
- Середня затримка між публікаціями (1 год 10 хв)
- Peak hour (11:00-13:00 - 5 публікацій)

**Engagement метрики:**
```
По кожному каналу:
- Views (перші 1 год, 24 год, загалом)
- Reactions (👍❤️🔥 тощо)
- Comments count
- Forwards count
- Engagement rate = (reactions + comments + forwards) / views

Агреговані:
- Total reach = сума підписників всіх каналів
- Average engagement rate
- Best performing channel
```

**Визначення першоджерела (складна логіка):**
```python
def identify_primary_source(story):
    pubs = story.publications.order_by('published_at')
    
    # Кандидат #1: Перший за часом
    first_pub = pubs[0]
    
    # Кандидат #2: Офіційне джерело
    official_pub = pubs.filter(
        channel__type='official'
    ).first()
    
    # Кандидат #3: Найдетальніший
    detailed_pub = max(pubs, key=lambda p: p.word_count)
    
    # Логіка пріоритизації:
    if official_pub and (
        official_pub.published_at - first_pub.published_at
    ).total_seconds() < 300:  # В межах 5 хв
        # Офіційне джерело опублікувало близько до першого
        return official_pub, "official"
    
    elif detailed_pub.word_count > first_pub.word_count * 2:
        # Набагато детальніша публікація
        # Можливо перший просто ретранслював короткий твіт
        return detailed_pub, "most_detailed"
    
    else:
        # Стандартно - хто першим
        return first_pub, "first_published"
```

**Географічне поширення:**
```python
# Якщо канали мають геотеги або можна визначити по контенту
{
    'regions': {
        'Київ': 5 каналів,
        'Львів': 1 канал,
        'Загальноукраїнські': 1 канал
    },
    'international': False
}
```

#### 2.2 Dashboard для каналів (безкоштовний)

**Доступ:**
Адміністратори каналів можуть зареєструватися через `/register_channel`

**Головна сторінка Dashboard:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 ANALYTICS DASHBOARD

Канал: Forbes Ukraine (@forbes_ua)
Період: Останні 30 днів

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 АУДИТОРІЯ В БОТІ
   1,234 користувачів моніторять ваш канал
   +187 за останні 7 днів (+17.8%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📰 ПОКРИТТЯ НОВИН
   347 ваших постів стали окремими новинами
   89 разів ви були ПЕРШОДЖЕРЕЛОМ (25.6%)
   258 разів підтвердили новини інших (74.4%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ ШВИДКІСТЬ РЕАКЦІЇ
   Середній час публікації: 12 хв після події
   
   Порівняння з категорією "Економіка":
   📊 [====|========] Ви: 12 хв | Середнє: 25 хв
   
   🏆 Рейтинг: #3 з 15 каналів

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 ДЕТАЛІЗАЦІЯ КОНТЕНТУ
   Середня довжина поста: 487 слів
   
   Порівняння з категорією:
   📊 [==========|==] Ви: 487 | Середнє: 215
   
   🏆 Рейтинг: #2 з 15 каналів (найдетальніше)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💬 ENGAGEMENT
   Середня engagement rate: 3.2%
   Total reactions за місяць: 45,234
   
   🏆 Рейтинг: #5 з 15 каналів

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 TRAFFIC З БОТА
   1,247 переходів на ваші оригінальні пости
   5.2% click-through rate (CTR)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 ТОП-5 ВАШИХ ТЕМ (по згадках в дайджестах)

1. Економічні реформи - 89 згадок
   Ви були першоджерелом: 23 рази
   
2. Стартап новини - 67 згадок
   Ви були першоджерелом: 34 рази
   
3. Інвестиції та фандрейзинг - 45 згадок
4. Курси валют та фінринки - 38 згадок
5. Бізнес персони України - 32 згадки

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 РЕКОМЕНДАЦІЇ

✅ Сильні сторони:
   • Висока деталізація - читачі цінують
   • Швидка реакція на події
   • Часто першоджерело у стартап-новинах

⚠️ Можливості для покращення:
   • Engagement нижче топ-3 конкурентів
   • Рідко покриваєте тему "Курси валют"
     (хоча є попит - 234 згадки загалом)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Детальна статистика] [Експорт даних] [Налаштування]
```

**Детальна статистика:**
```
📊 ДЕТАЛЬНА СТАТИСТИКА

Оберіть період:
[Сьогодні] [7 днів] [30 днів] [Custom]

Оберіть метрику:
• Кількість користувачів (динаміка)
• Покриття новин (графік)
• Швидкість публікації (histogram)
• Engagement по темах
• Порівняння з конкурентами

[Графіки та візуалізації]

[Експорт в CSV] [Експорт в Excel]
```

**Сповіщення для каналу:**
```
🎉 Ваш пост став trending!

"Нова економічна реформа"

📊 Статистика за 2 години:
   • 7 каналів підтвердили
   • 45K загальний reach
   • Ви були ПЕРШОДЖЕРЕЛОМ
   
[Подивитися детальніше]
```

#### 2.3 Генерація подкастів

**Технологія:**
- ElevenLabs API для якісного TTS
- Альтернатива: Google Cloud TTS (дешевше)

**Формати:**
- Короткий (5 хв) - топ-3 новини дня
- Стандартний (10 хв) - топ-10 новин
- Повний (20 хв) - всі новини з деталями

**Процес генерації:**
```python
async def generate_podcast(user_digest):
    # 1. Створюємо сценарій для подкасту
    script = create_podcast_script(user_digest)
    
    # 2. Додаємо інтонації та паузи
    script_with_ssml = add_intonation(script)
    
    # 3. Генеруємо аудіо через TTS
    audio = await elevenlabs.generate(
        text=script_with_ssml,
        voice="Antoni",  # або інший голос
        model="eleven_multilingual_v2"
    )
    
    # 4. Зберігаємо та повертаємо посилання
    audio_url = save_audio(audio, user_id, date)
    return audio_url

def create_podcast_script(digest):
    """Створює сценарій для озвучування"""
    
    intro = """
    Доброго вечора! Це ваш новинний дайджест 
    за п'ятнадцяте лютого дві тисячі двадцять шостого року.
    
    <break time="1s"/>
    
    Сьогодні у нас {count} найважливіших новин.
    
    <break time="1s"/>
    """.format(count=len(digest.items))
    
    body = ""
    for i, item in enumerate(digest.items):
        body += f"""
        Новина номер {i+1}.
        
        <emphasis level="strong">{item.title}</emphasis>
        
        <break time="0.5s"/>
        
        {item.summary}
        
        <break time="1s"/>
        
        Ця новина з'явилася в каналах: 
        {', '.join([s.channel.title for s in item.sources[:3]])}
        {' та інших' if len(item.sources) > 3 else ''}
        
        <break time="1.5s"/>
        """
    
    outro = """
    Це були головні новини дня. 
    Детальніше читайте в дайджесті в боті.
    
    <break time="1s"/>
    
    Гарного вечора!
    """
    
    return intro + body + outro
```

**UI для користувача:**
```
🎧 АУДІО ДАЙДЖЕСТ

Твій дайджест за 15 лютого готовий!

📝 Текстова версія (12 новин)
[Читати →]

🎙 Аудіо версія (9 хв 23 сек)
[▶️ Слухати] [⬇️ Завантажити]

Голос: Чоловічий (Ukrainian)
[Змінити голос в налаштуваннях]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎧 ПОПЕРЕДНІ ПОДКАСТИ

14.02 - 8 хв 15 сек [▶️]
13.02 - 11 хв 02 сек [▶️]
12.02 - 7 хв 43 сек [▶️]

[Показати більше]
```

**Налаштування подкастів:**
```
🎙 НАЛАШТУВАННЯ ПОДКАСТІВ

🗣 Голос:
   ◉ Чоловічий український
   ○ Жіночий український
   ○ Нейтральний
   [Прослухати зразки]

⏱ Довжина:
   ○ Коротко (5 хв, топ-3)
   ◉ Стандарт (10 хв, топ-10)
   ○ Повний (20 хв, всі новини)

🎵 Стиль:
   ◉ Новинний (офіційний тон)
   ○ Розмовний (casual)
   ○ Динамічний (швидкий темп)

📱 Автогенерація:
   ☑ Генерувати щодня разом з текстом
   ☐ Тільки за запитом

💾 Зберігання:
   Зберігати останні [7] днів
```

**Витрати на подкасти:**
```
ElevenLabs ціни:
- Free tier: 10K символів/міс (недостатньо)
- Creator: $22/міс для 120K символів
- Pro: $99/міс для 660K символів

Для 10-хв подкасту потрібно ~1,500 символів
= ~$0.30 на подкаст (Creator план)

Google Cloud TTS (дешевше):
- $16 за 1M символів
- 10-хв подкаст = 1,500 символів = $0.024

Рекомендація для MVP: Google TTS
Рекомендація для Premium: ElevenLabs
```

### KPI для завершення Фази 2

**Користувачі:**
- 2,000+ активних користувачів
- 60%+ користують подкасти (з тих хто включив)
- 75%+ retention за місяць

**Канали:**
- 20+ каналів зареєструвалися в dashboard
- 50+ каналів активно моніторяться
- Позитивний feedback від адмінів каналів

**Технічні:**
- Analytics dashboard працює стабільно
- Подкасти генеруються за <2 хвилини
- Витрати на TTS <$0.05 на користувача

---

## ФАЗА 3: Партнерська програма (Місяці 7-9)

### Мета
Запустити перші партнерства з каналами. Почати monetization.

### 3.1 Партнерська програма

**Структура програми:**

#### Tier 1: Basic Partnership (безкоштовно)

**Що отримує канал:**
- ✅ Включення в каталог
- ✅ Стандартний опис (100 символів)
- ✅ Показ в категорії
- ✅ Attribution в дайджестах
- ✅ Базовий analytics dashboard

**Що просимо:**
- 📣 1 рекламний пост про бота

**Шаблон посту:**
```
🤖 Не встигаєте читати всі новинні канали?

@[YourBot] збирає новини з ваших улюблених 
каналів і робить короткий дайджест щодня.

✨ Що вміє:
• Автоматично відстежує обрані канали
• Прибирає дублікати (одна новина - один запис)
• Показує хто першоджерело і як поширювалася
• Щовечора дайджест у зручному форматі
• Можна слухати як подкаст 🎧

Додати канали просто - форвардни будь-який 
пост і він автоматично додасться.

Наш канал вже в каталозі 👆

[Спробувати безкоштовно] → @[YourBot]
```

#### Tier 2: Premium Partnership

**Що отримує канал:**
- ✅ Все з Basic +
- ✅ 🌟 Бейдж "Featured Partner"
- ✅ Пріоритетна позиція в категорії (топ-3)
- ✅ Розширений опис (300 символів) + логотип
- ✅ Згадки в weekly highlights
- ✅ Advanced analytics dashboard
- ✅ Персональний менеджер

**Що просимо:**
- 📣 2 рекламні пости (старт + через місяць)
- 📌 Постійний лінк в описі каналу
- 🤝 Co-marketing можливості

**Або платна опція:** $50-100/міс

#### Tier 3: Platinum Partnership

**Що отримує канал:**
- ✅ Все з Premium +
- ✅ 💎 Бейдж "Official Partner"
- ✅ Ексклюзивна позиція (1 на категорію)
- ✅ Featured в onboarding flow
- ✅ Спільні маркетингові кампанії
- ✅ Whitelabel analytics можливості
- ✅ API доступ до даних

**Ціна:** $200-500/міс або individual terms

### 3.2 Платні опції для каналів

#### Featured Placement - $50-100/міс

**Що входить:**
```
📍 ТОП ПОЗИЦІЯ В КАТЕГОРІЇ

Ваш канал:
• Завжди в топ-3 при виборі категорії
• Виділений іншим кольором/бейджем
• Показується в "Рекомендовані"
• Priority в алгоритмі рекомендацій
```

**ROI для каналу:**
- Очікуваний приріст: +100-300 підписників/міс
- Cost per subscriber: $0.30-1.00
- Lifetime value підписника: $5-20 (за оцінками)

#### Premium Analytics - $99/міс

**Що входить:**
```
📊 РОЗШИРЕНА АНАЛІТИКА

Додатково до безкоштовної версії:

• Поглиблені insights по аудиторії:
  - Демографія користувачів боту
  - Які ще канали вони читають
  - Паттерни читання (час, дні тижня)
  
• Конкурентний аналіз:
  - Детальне порівняння з топ-10 у категорії
  - Benchmarking по всіх метриках
  - Gaps і opportunities
  
• Predictive analytics:
  - Прогноз трендових тем
  - Рекомендації по темах для покриття
  - Best time to post
  
• Експорт і інтеграції:
  - API доступ до своїх даних
  - Webhooks для real-time alerts
  - Інтеграція з Google Analytics
  
• Historical data:
  - Дані за весь період (не тільки 30 днів)
  - Тренди та паттерни
```

#### Sponsored Digest - $300-500 за дайджест

**Що входить:**
```
💎 СПОНСОРУВАННЯ ДАЙДЖЕСТУ

Ваш канал спонсорує дайджест на 1 день:

• Header брендинг:
  "Дайджест за 15 лютого
   за підтримки Forbes Ukraine"

• Ваша новина першою (якщо покрили тему)

• Спеціальне виділення:
  "💎 ЕКСКЛЮЗИВ від партнера
   Forbes Ukraine опублікував детальний
   аналіз з інфографікою та коментарями
   5 експертів. [Читати повністю →]"

• Охоплення: ~2,000 користувачів
```

#### Promoted Story - $100-200

**Що входить:**
```
🚀 ПРОСУВАННЯ КОНКРЕТНОЇ НОВИНИ

Виберіть свою найкращу публікацію
і ми дамо їй boost:

• Push notification всім користувачам
  (навіть тим хто не підписаний на вас)
  
• Priority в дайджесті (топ-3 гарантовано)

• Спеціальний бейдж "Must Read"

• Детальна аналітика ефективності
```

### 3.3 Процес залучення партнерів

**Етап 1: Outreach (Місяць 7)**

**Таргет:** 30 mid-tier каналів (30K-200K підписників)

**Чому mid-tier:**
- Дуже мотивовані рости
- Більш відкриті до експериментів
- Легше домовитися
- Можуть стати амбасадорами

**Email/DM template:**
```
Тема: Партнерство: [YourBot] × [Channel Name]

Привіт команда [Channel Name]!

Я [Ім'я], засновник [YourBot] - Telegram бота 
який допомагає людям не пропускати важливі новини.

Ми автоматично моніторимо топ-канали, збираємо 
схожі новини в одну, і робимо персональні дайджести 
для кожного користувача.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Трохи цифр:
• 2,000+ активних користувачів
• 50+ каналів в каталозі
• 80%+ відкривають щоденні дайджести

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Чому пишу вам:

[Channel Name] - один з найкращих каналів в 
категорії [Category]. Ми хочемо додати вас в 
наш каталог як Featured Partner.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Що це дасть вам:

1. Нова зацікавлена аудиторія
   ~2,000 потенційних підписників побачать вас

2. Додатковий трафік
   Ми направляємо на ваші найкращі матеріали
   (середня CTR: 5.2%)

3. Конкурентна аналітика
   Ви побачите як виглядаєте проти інших каналів
   у категорії (швидкість, деталізація, engagement)

4. Credibility boost
   Бейдж "Featured Partner" підвищує довіру

5. Zero cost
   Все що потрібно - один пост про нас

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Ось як це виглядає для вас:

[Screenshot analytics dashboard]
[Screenshot attribution в дайджесті]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤝 Що далі?

Якщо цікаво - давайте обговоримо деталі.
Можу показати повний demo та відповісти на питання.

Також маю кілька ідей для спільних 
маркетингових активностей 🚀

Чекаю на відповідь!

З повагою,
[Ваше ім'я]

P.S. Ось посилання на бота для швидкого огляду:
@[YourBot]
```

**Етап 2: Demo & Discussion**

Підготувати:
- Презентація продукту (10 слайдів)
- Live demo в Telegram
- Mock-up analytics dashboard для їх каналу
- Case study (якщо вже є партнери)

**Етап 3: Contract & Launch**

**Простий партнерський договір:**
```
ПАРТНЕРСЬКА УГОДА

Сторони:
1. [YourBot] (далі - Бот)
2. [Channel Name] (далі - Канал)

Предмет угоди:
Бот включає Канал в свій каталог як Featured Partner

Зобов'язання Бота:
• Додати Канал в каталог з позначкою Featured
• Показувати Канал в категорії [Category]
• Надати доступ до Analytics Dashboard
• Показувати attribution в дайджестах

Зобов'язання Каналу:
• Опублікувати 1 рекламний пост про Бот
  протягом 7 днів після підписання
• [Опційно] Додати посилання на Бот в опис каналу

Термін дії: 6 місяців з можливістю продовження

Підписи:
_______________  _______________
```

**Post-launch:**
- Моніторинг результатів
- Щотижневі звіти партнеру
- Adjustments based on feedback

### 3.4 Monetization через користувачів

**Free Tier:**
```
🆓 БЕЗКОШТОВНО

✅ 10 каналів
✅ Щоденний дайджест (текст)
✅ Базова персоналізація
✅ Додавання через forward
✅ Attribution джерел
```

**Pro Tier - $4.99/міс:**
```
⭐ PRO ПЛАН

✅ Необмежена кількість каналів
✅ Дайджест 2 рази на день
✅ 🎧 Аудіо подкасти
✅ Детальна аналітика поширення
✅ Push для trending новин
✅ Кастомізація:
   - Вибір категорій
   - Налаштування часу
   - Фільтри по джерелах
✅ Експорт дайджестів
✅ Ad-free experience
```

**Business Tier - $19.99/міс:**
```
💼 BUSINESS ПЛАН

✅ Все з Pro +
✅ Моніторинг приватних каналів (скоро)
✅ Групи та обговорення
✅ API доступ
✅ Білі дайджести з вашим брендом
✅ Team management (до 5 користувачів)
✅ Priority support
✅ Custom integrations
```

**Conversion strategy:**
```
День 1-7: Користувач на Free
  └─ Повна функціональність, никаких обмежень
  └─ Мета: влюбити в продукт

День 8: Soft prompt
  └─ "Хочеш слухати дайджести як подкасти? 
      Спробуй Pro безкоштовно 7 днів"

День 15: Hard limit
  └─ "Ти додав 10 каналів (ліміт Free плану).
      Upgrade до Pro для необмежених каналів"

День 30: Re-engagement
  └─ "Ти пропустив дайджест вчора.
      З Pro можеш отримувати 2 на день"
```

### KPI для завершення Фази 3

**Partnerships:**
- ✅ 10+ active basic partnerships
- ✅ 3+ premium partnerships
- ✅ 1+ platinum partnership
- ✅ 5+ платних featured placements

**Revenue:**
- ✅ $1,000+ MRR від користувачів
- ✅ $500+ MRR від каналів
- ✅ $1,500+ total MRR

**Користувачі:**
- ✅ 5,000+ активних користувачів
- ✅ 10%+ conversion Free → Pro
- ✅ 70%+ retention на Pro

---

## ФАЗА 4: Масштабування (Місяці 10+)

### Мета
Вийти на стійку бізнес-модель. Масштабувати на інші ринки.

### 4.1 Автоматизація партнерської програми

**Self-serve платформа для каналів:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 PARTNERSHIP PLATFORM

Для адміністраторів каналів
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Крок 1: Верифікація каналу
  • Підтвердіть що ви адмін каналу
  • Пост з кодом підтвердження
  • [Верифікувати] →

Крок 2: Оберіть план
  
  ☐ Basic (безкоштовно)
     1 рекламний пост
     
  ☐ Featured ($50/міс)
     Пріоритетна позиція
     
  ☐ Premium ($99/міс)
     Featured + Advanced analytics
  
Крок 3: Налаштування
  • Опис каналу (300 символів)
  • Логотип
  • Категорія
  • Ключові слова

Крок 4: Публікація
  • Ми згенеруємо рекламний пост
  • Або використайте свій
  • Опублікуйте в каналі

Крок 5: Активація
  • Після верифікації посту
  • Ваш канал з'явиться в каталозі
  • Доступ до analytics dashboard

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Автоматизовані features:**
- Верифікація через бота (канал постить код)
- Автоматичне Invoice через Stripe
- Self-service dashboard
- Автоматична публікація в каталог
- Email/Telegram нотифікації про результати

### 4.2 API для B2B

**Use cases:**

**1. Медіа компанії:**
- Інтегрувати моніторинг в свої CMS
- Автоматично отримувати trending topics
- Competitor analysis

**2. PR агенції:**
- Моніторинг згадок клієнтів
- Аналіз поширення новин
- Генерація звітів

**3. Аналітичні компанії:**
- Дані для досліджень
- Trend analysis
- Sentiment analysis

**API Endpoints:**
```
GET /api/v1/stories
  - Отримати новини за період
  - Фільтри: category, channels, date range
  
GET /api/v1/stories/{id}
  - Детальна інформація про новину
  - Всі публікації, метрики, timeline

GET /api/v1/stories/{id}/analytics
  - Аналітика поширення
  - Першоджерело, швидкість, engagement

GET /api/v1/channels
  - Список каналів
  - Метрики каналів

GET /api/v1/channels/{id}/stories
  - Новини конкретного каналу
  
POST /api/v1/digest/generate
  - Згенерувати custom дайджест
  - Параметри: channels[], categories[], format

Webhooks:
POST /webhooks/story-verified
  - Коли новина verified
POST /webhooks/story-trending
  - Коли новина trending
```

**Pricing:**
```
🔑 API ACCESS

Starter: $99/міс
  • 10K requests/міс
  • Базові endpoints
  • Email support

Pro: $299/міс
  • 100K requests/міс
  • Всі endpoints
  • Webhooks
  • Priority support

Enterprise: Custom
  • Необмежені requests
  • Dedicated infrastructure
  • SLA гарантії
  • Custom features
```

### 4.3 Розширення географії

**Етап 1: Російськомовні канали**
- Росія, Білорусь, Казахстан
- ~500M потенційних користувачів
- Ті ж технології, інший каталог

**Етап 2: Англомовні канали**
- США, UK, глобальні новини
- Найбільший ринок
- Більша конкуренція

**Етап 3: Інші мови**
- Польща (український діаспора)
- Німеччина
- По запиту

**Локалізація:**
- Переклад UI
- Локальні каталоги каналів
- Окремі промпти для LLM (враховують культурний контекст)
- Локальна підтримка

### 4.4 Свій медіа-канал (опційно)

**Коли запускати:** Після досягнення:
- 10,000+ користувачів боту
- 30+ active partnerships
- Стабільна технологія

**Концепція:**

```
@NewsVerified

Теглайн: "Перевірені новини з 100+ джерел"

Формат:
• Тільки новини з 3+ підтвердженнями
• Хронологічний порядок
• Attribution до всіх джерел
• Мета-аналіз (хто швидше, детальніше)
• Transparency (відкрита методологія)

Приклад поста:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 12:47 | ВЕРИФІКОВАНО

Нова економічна реформа

[Короткий зміст 100-150 слів]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Підтверджено: 7 джерел за 4 години

⚡ Першоджерело:
@minfin_ua (11:23)

📝 Найдетальніше:
@forbes_ua (487 слів)

📢 Також покрито:
@economichna_p | @nv_business | @mc_today
@ain_ua | @delo_ua

[Детальніше в боті] → @[YourBot]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Monetization каналу:**
- Реклама (CPM $5-10)
- Sponsored posts від партнерів ($200-500)
- Premium content (платна підписка)
- Cross-sell на бота

**Позиціонування:**
- НЕ конкурент каналам
- Мета-агрегатор
- "Найперевіреніший канал України"
- Направляє трафік до джерел

### 4.5 White-label рішення

**Для кого:**
- Великі медіа компанії (УП, НВ, Forbes)
- Корпорації (внутрішні дайджести)
- Університети (academic digests)

**Що пропонуємо:**
```
📦 WHITE-LABEL SOLUTION

Ваш власний branded бот на нашій технології:

✅ Повна кастомізація:
   • Ваше ім'я, лого, брендинг
   • Custom onboarding
   • Ваші кольори та стиль

✅ Технологічна платформа:
   • Моніторинг каналів
   • Кластеризація новин
   • AI резюмування
   • Analytics

✅ Ваш контроль:
   • Вибір джерел
   • Модерація контенту
   • Власні правила кластеризації

✅ Support & updates:
   • Технічна підтримка
   • Регулярні оновлення
   • Масштабування

Ціна: $2,000-10,000/міс
+ Revenue share або fixed fee
```

**Приклад use case:**

**"Forbes Ukraine News Bot"**
- Branded бот від Forbes
- Моніторить Forbes + обрані партнери
- Forbes контент завжди featured
- Дайджести в стилі Forbes
- Monetization: підписка + реклама
- Forbes отримує: engagement tool, додатковий revenue stream

### Revenue Projections (Фаза 4)

**Користувачі:**
```
10,000 активних користувачів
├─ 8,000 Free (0)
├─ 1,500 Pro ($4.99) = $7,485/міс
└─ 500 Business ($19.99) = $9,995/міс

User revenue: $17,480/міс
```

**Канали:**
```
50 партнерів:
├─ 30 Basic (безкоштовно) = $0
├─ 15 Featured ($50) = $750/міс
└─ 5 Premium ($99) = $495/міс

Додатково:
├─ Sponsored digests (4/міс × $400) = $1,600/міс
├─ Analytics subscriptions (10 × $99) = $990/міс

Channel revenue: $3,835/міс
```

**B2B/API:**
```
3 API клієнти:
├─ 1 Starter ($99)
├─ 1 Pro ($299)
└─ 1 Enterprise ($999)

API revenue: $1,397/міс
```

**White-label:**
```
1-2 клієнти × $5,000 = $5,000-10,000/міс
```

**Total MRR: $28,000-33,000**

**Витрати:**
```
Infrastructure: $500-1,000/міс
LLM API: $1,500-2,500/міс
TTS (подкасти): $500-800/міс
Team (2-3 people): $5,000-8,000/міс
Marketing: $2,000-3,000/міс
Other: $500-1,000/міс

Total costs: $10,000-16,300/міс

Net profit: $12,000-23,000/міс
```

---

## Технічні детали та Best Practices

### Оптимізація витрат на LLM

**Стратегії зниження витрат:**

1. **Використання cheaper models де можливо:**
```
Задача | Модель | Вартість
─────────────────────────────────────
Кластеризація | Embeddings | $0.13/1M tokens
Короткі саммарі | Haiku | $0.25/1M input
Повні саммарі | Sonnet | $3/1M input
Складні аналізи | Opus | $15/1M input
```

2. **Batch processing:**
- Збирати пости протягом години
- Обробляти разом (1 API call замість 50)
- Економія 40-50%

3. **Caching:**
- Кешувати embeddings постів
- Зберігати саммарі для reuse
- Не regenerate якщо контент не змінився

4. **Prompt optimization:**
```
Погано (багато токенів):
"Прочитай всі ці пости і створи детальне 
резюме що включає всі ключові факти, контекст, 
імена, цифри та висновки..."
[15 постів по 500 слів кожен = 7500 слів input]

Добре (менше токенів):
"Створи резюме (150-200 слів) з постів:
Post 1: [витяг ключових 50 слів]
Post 2: [витяг ключових 50 слів]
...
[Загалом 750 слів input]

Focus: головна подія, цифри, implications"
```

5. **Tiered summarization:**
```
Перевірені новини (2+ джерела):
  → Повне резюме (дорога модель)
  
Pending новини (1 джерело):
  → Базове резюме (дешева модель)
  → Update до повного коли verified
```

### Масштабування infrastructure

**При 1,000 користувачів:**
- 1 server (2 CPU, 4GB RAM)
- PostgreSQL на тому ж сервері
- Redis на тому ж сервері
- 2 Celery workers

**При 10,000 користувачів:**
- 2-3 app servers (load balanced)
- Dedicated PostgreSQL (4 CPU, 16GB RAM)
- Dedicated Redis
- 5-10 Celery workers
- CDN for audio files (подкасти)

**При 100,000 користувачів:**
- 10+ app servers
- PostgreSQL cluster (read replicas)
- Redis cluster
- 50+ Celery workers
- Separate services:
  - Monitoring service
  - Analytics service
  - API gateway
  - Background jobs queue

**Database optimization:**
```sql
-- Індекси для швидких запитів
CREATE INDEX idx_stories_status ON stories(status);
CREATE INDEX idx_stories_date ON stories(first_seen_at);
CREATE INDEX idx_publications_channel ON story_publications(channel_id);
CREATE INDEX idx_publications_date ON story_publications(published_at);

-- Partition великих таблиць по датах
CREATE TABLE story_publications_2026_02 
PARTITION OF story_publications
FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- Vector index для швидкого similarity search
CREATE INDEX ON stories USING ivfflat (embedding_vector vector_cosine_ops);
```

### Security & Privacy

**Дані користувачів:**
- Зберігаємо мінімум (user_id, preferences)
- НЕ зберігаємо історію прочитаного
- НЕ продаємо дані третім особам
- GDPR compliant (право на видалення)

**Дані каналів:**
- Публічні пости - fair use
- Не копіюємо повний контент (тільки metadata)
- Attribution до джерел
- Право каналу opt-out

**API security:**
- Rate limiting
- API keys з обмеженими правами
- Webhook signature verification
- HTTPS everywhere

---

## Marketing & Growth Strategy

### Launch Strategy (Фаза 1)

**Pre-launch (2 тижні до):**
1. Landing page з waitlist
2. Product Hunt submission готово
3. Список потенційних early adopters
4. Partnerships з 3-5 мікро-інфлюенсерами

**Launch day:**
1. Product Hunt
2. Reddit (r/ukraine, r/Ukrainian тощо)
3. Twitter/X thread
4. Telegram groups/chats (де дозволено)
5. Email до waitlist

**Post-launch (тижні 1-4):**
1. Content marketing:
   - "Як не загубитися в 50 Telegram каналах"
   - "Топ-20 українських новинних каналів"
   - "Як ми використовуємо AI для верифікації новин"

2. Community building:
   - Telegram група користувачів
   - Збір feedback
   - Feature requests

3. PR:
   - Статті в tech медіа (AIN, DOU)
   - Подкасти про стартапи
   - Інтерв'ю з засновниками

### Growth loops

**Loop 1: Viral через forward**
```
Користувач → Форвардить пост з каналу →
Бот обробляє → Пропонує боту друзям →
Новий користувач
```

**Loop 2: Partnerships**
```
Більше користувачів → Цінність для каналів →
Канали роблять рекламу → Більше користувачів
```

**Loop 3: Content marketing**
```
Генеруємо insights з даних → Публікуємо →
Traffic → Нові користувачі → Більше даних
```

### Metrics to track

**Користувачі:**
- Daily Active Users (DAU)
- Weekly Active Users (WAU)
- Monthly Active Users (MAU)
- DAU/MAU ratio (engagement)
- Retention (D1, D7, D30)
- Churn rate

**Продукт:**
- Avg channels per user
- Digest open rate
- Digest read time
- Forward-to-add conversion
- Pro conversion rate

**Бізнес:**
- MRR (Monthly Recurring Revenue)
- ARR (Annual Recurring Revenue)
- LTV (Lifetime Value)
- CAC (Customer Acquisition Cost)
- LTV/CAC ratio

**Канали:**
- Active partnerships
- Partnership retention
- Revenue per partner
- Traffic to partners

---

## Risks & Mitigation

### Technical Risks

**Risk 1: Погана якість кластеризації**
- Mitigation: A/B тестинг різних thresholds
- Митigation: Human-in-the-loop для складних випадків
- Mitigation: ML model improvement з часом

**Risk 2: Витрати на LLM out of control**
- Mitigation: Жорсткі ліміти на token usage
- Mitigation: Cheaper models де можливо
- Mitigation: Caching агресивно

**Risk 3: Telegram API changes**
- Mitigation: Стежити за announcements
- Mitigation: Мати fallback план
- Mitigation: Diversify (не тільки Telegram eventually)

### Business Risks

**Risk 1: Telegram запускає native feature**
- Mitigation: Focus на персоналізацію (вони не зроблять)
- Mitigation: B2B pivot можливий
- Mitigation: First mover advantage

**Risk 2: Copy-cats**
- Mitigation: Швидка ітерація
- Mitigation: Partnerships як moat
- Mitigation: Data advantage (більше користувачів = кращі insights)

**Risk 3: Канали не хочуть партнерства**
- Mitigation: Доказати value з даних
- Mitigation: Почати з smaller каналів
- Mitigation: Alternative monetization (не залежати тільки від партнерств)

### Legal Risks

**Risk 1: Порушення ToS Telegram**
- Mitigation: Використовувати офіційні API
- Mitigation: Rate limits дотримувати
- Mitigation: Консультація з юристом

**Risk 2: Copyright issues**
- Mitigation: Fair use (короткі витяги)
- Mitigation: Attribution завжди
- Mitigation: Opt-out для каналів

**Risk 3: GDPR/Privacy**
- Mitigation: Мінімум персональних даних
- Mitigation: Clear privacy policy
- Mitigation: Right to be forgotten

---

## Success Metrics по Фазах

### Фаза 1 Success (MVP):
- ✅ 500+ активних користувачів
- ✅ 70%+ retention тиждень
- ✅ Product-market fit validated
- ✅ <$1 CAC
- ✅ Positive user feedback

### Фаза 2 Success (Analytics):
- ✅ 2,000+ користувачів
- ✅ 20+ каналів в dashboard
- ✅ Подкасти працюють стабільно
- ✅ 60%+ користують audio
- ✅ Готові до partnerships

### Фаза 3 Success (Partnerships):
- ✅ 10+ active partnerships
- ✅ $1,500+ MRR
- ✅ 5,000+ користувачів
- ✅ 10%+ paid conversion
- ✅ Позитивний ROI

### Фаза 4 Success (Scale):
- ✅ $30,000+ MRR
- ✅ 10,000+ користувачів
- ✅ 50+ partnerships
- ✅ Profitable
- ✅ Ready for investment (optional)

---

## Команда (рекомендації)

### Фаза 1 (MVP):
- 1-2 Full-stack розробники
- (Опційно: 1 part-time дизайнер)

### Фаза 2-3:
- 2 Backend developers
- 1 Full-stack developer (web dashboard)
- 1 Product/Marketing person
- (Опційно: 1 ML engineer)

### Фаза 4:
- 3-4 Engineers
- 1 Product Manager
- 1 Marketing/Growth
- 1 Partnership Manager
- 1 Customer Support

---

## Висновок

Це амбітний але реалістичний план. Ключові моменти:

**Strengths:**
- ✅ Чітка поетапність
- ✅ Focus на користувачів спочатку
- ✅ Multiple revenue streams
- ✅ Scalable архітектура
- ✅ Унікальна цінність (forward-to-add, verification)

**Critical success factors:**
1. Якість кластеризації (технологія)
2. User retention (продукт)
3. Partnerships (бізнес)
4. Швидкість execution (конкуренти)

**Timeline summary:**
- Місяці 1-3: MVP & launch
- Місяці 4-6: Analytics & podcasts
- Місяці 7-9: Partnerships & monetization
- Місяці 10+: Scale & new markets

**Go/No-go критерії:**
Після кожної фази оцінюємо чи продовжувати:
- Фаза 1: Чи є product-market fit?
- Фаза 2: Чи цікаво каналам?
- Фаза 3: Чи працює monetization?
- Фаза 4: Чи можна scale profitable?

---

## Прогрес (21.02.2026)

- [x] **Mini App UX**: Реалізовано Infinite Scroll та покращено систему фільтрації.
- [x] **Theme System**: Повна підтримка світлої теми та Telegram integration.
- [x] **Backend Fixes**: Оптимізація логіки дайджесту для великих списків новин.

Успіхів у реалізації! 🚀
