# Pulse Bot - Технічне завдання для розробки

## Огляд проекту

**Назва:** Pulse News Bot  
**Username:** @pulse_daily_bot  
**Мета:** Telegram-бот для автоматичного збору, агрегації та резюмування новин з публічних Telegram-каналів

**Основна цінність:**
- Моніторинг обраних користувачем каналів 24/7
- Автоматична дедуплікація новин (одна новина з багатьох джерел)
- Верифікація через підтвердження з кількох джерел
- Персоналізовані щоденні дайджести
- Додавання каналів одним форвардом (killer feature)

---

## Фази розробки

Проект розділено на 4 фази. Це ТЗ покриває **Фазу 1 (MVP)**.

**MVP Timeline:** 2-3 місяці  
**MVP Goal:** 500+ активних користувачів, proof of concept

---

## Технічний стек

### Backend
- **Мова:** Python 3.11+
- **Bot Framework:** aiogram 3.x
- **Моніторинг каналів:** Telethon (Telegram Client API)
- **База даних:** PostgreSQL 14+ з pgvector extension
- **Черга завдань:** Celery + Redis
- **Кешування:** Redis
- **LLM API:** Anthropic Claude (Haiku для MVP, Sonnet для production)
- **Embeddings:** OpenAI text-embedding-3-small або Cohere
- **Environment:** Docker + Docker Compose

### Infrastructure (рекомендовано)
- **Хостинг:** Railway, Fly.io, або DigitalOcean
- **Мінімальні ресурси:** 2 CPU, 4GB RAM, 20GB SSD
- **Scaling:** 10,000 users = 4 CPU, 16GB RAM

### Development Tools
- **Version Control:** Git + GitHub
- **Environment Management:** python-venv або poetry
- **Linting:** ruff або black + flake8
- **Testing:** pytest

---

## Архітектура системи

```
┌─────────────────────────────────────────────────────────┐
│                    USER (Telegram)                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              TELEGRAM BOT API (aiogram)                 │
│  - Обробка команд (/start, /add, /channels)           │
│  - Forward handler (додавання каналів)                 │
│  - Inline keyboards                                     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                 APPLICATION LAYER                       │
│  - Business logic                                       │
│  - User management                                      │
│  - Channel subscriptions                                │
└──────────────────────┬──────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  PostgreSQL │ │    Redis    │ │   Celery    │
│             │ │             │ │   Workers   │
│  - Users    │ │  - Cache    │ │             │
│  - Channels │ │  - Sessions │ │  - Monitor  │
│  - Stories  │ │  - Queue    │ │  - Cluster  │
│  - Pubs     │ │             │ │  - Summarize│
└─────────────┘ └─────────────┘ └──────┬──────┘
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │   TELETHON CLIENT    │
                            │  Channel Monitoring  │
                            └──────────────────────┘
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │   EXTERNAL APIS      │
                            │  - Claude API        │
                            │  - OpenAI Embeddings │
                            └──────────────────────┘
```

---

## База даних - детальна схема

### Таблиця: users

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language_code VARCHAR(10) DEFAULT 'uk',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    is_premium BOOLEAN DEFAULT false,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    digest_time TIME DEFAULT '20:00:00',
    digest_frequency VARCHAR(20) DEFAULT 'daily',
    timezone VARCHAR(50) DEFAULT 'Europe/Kiev'
);

CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;
```

### Таблиця: channels

```sql
CREATE TABLE channels (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    subscribers_count INTEGER,
    category VARCHAR(100),
    is_public BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    avg_post_frequency FLOAT,
    credibility_score FLOAT DEFAULT 0.5,
    partnership_status VARCHAR(50) DEFAULT 'none',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_channels_telegram_id ON channels(telegram_id);
CREATE INDEX idx_channels_username ON channels(username) WHERE username IS NOT NULL;
CREATE INDEX idx_channels_category ON channels(category);
CREATE INDEX idx_channels_public ON channels(is_public) WHERE is_public = true;
```

### Таблиця: user_subscriptions

```sql
CREATE TABLE user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_method VARCHAR(50), -- 'catalog', 'forward', 'link', 'search'
    is_active BOOLEAN DEFAULT true,
    notification_enabled BOOLEAN DEFAULT true,
    UNIQUE(user_id, channel_id)
);

CREATE INDEX idx_subscriptions_user ON user_subscriptions(user_id);
CREATE INDEX idx_subscriptions_channel ON user_subscriptions(channel_id);
CREATE INDEX idx_subscriptions_active ON user_subscriptions(user_id, is_active);
```

### Таблиця: stories (новини)

```sql
CREATE TABLE stories (
    id SERIAL PRIMARY KEY,
    title TEXT,
    summary TEXT,
    category VARCHAR(100),
    first_seen_at TIMESTAMP NOT NULL,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_score FLOAT DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'pending', -- pending, verified, trending, archived
    embedding_vector VECTOR(1536), -- для pgvector
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stories_status ON stories(status);
CREATE INDEX idx_stories_first_seen ON stories(first_seen_at);
CREATE INDEX idx_stories_category ON stories(category);

-- Vector index для швидкого similarity search
CREATE INDEX ON stories USING ivfflat (embedding_vector vector_cosine_ops)
WITH (lists = 100);
```

### Таблиця: story_publications (публікації)

```sql
CREATE TABLE story_publications (
    id SERIAL PRIMARY KEY,
    story_id INTEGER REFERENCES stories(id) ON DELETE CASCADE,
    channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
    post_id BIGINT NOT NULL,
    post_url TEXT,
    original_text TEXT NOT NULL,
    published_at TIMESTAMP NOT NULL,
    reactions_count INTEGER DEFAULT 0,
    views_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    forwards_count INTEGER DEFAULT 0,
    word_count INTEGER,
    has_media BOOLEAN DEFAULT false,
    media_urls TEXT[],
    embedding_vector VECTOR(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel_id, post_id)
);

CREATE INDEX idx_publications_story ON story_publications(story_id);
CREATE INDEX idx_publications_channel ON story_publications(channel_id);
CREATE INDEX idx_publications_published ON story_publications(published_at);
CREATE INDEX idx_publications_channel_post ON story_publications(channel_id, post_id);

-- Vector index
CREATE INDEX ON story_publications USING ivfflat (embedding_vector vector_cosine_ops)
WITH (lists = 100);
```

### Таблиця: story_analytics (агреговані дані)

```sql
CREATE TABLE story_analytics (
    story_id INTEGER PRIMARY KEY REFERENCES stories(id) ON DELETE CASCADE,
    total_publications INTEGER DEFAULT 0,
    unique_channels INTEGER DEFAULT 0,
    first_channel_id INTEGER REFERENCES channels(id),
    first_published_at TIMESTAMP,
    peak_publication_time TIMESTAMP,
    total_reach BIGINT DEFAULT 0,
    total_reactions INTEGER DEFAULT 0,
    total_views INTEGER DEFAULT 0,
    avg_engagement_rate FLOAT DEFAULT 0.0,
    spread_velocity FLOAT DEFAULT 0.0, -- publications per hour
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analytics_story ON story_analytics(story_id);
```

### Таблиця: user_digests (історія дайджестів)

```sql
CREATE TABLE user_digests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    digest_date DATE NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    stories_count INTEGER DEFAULT 0,
    was_opened BOOLEAN DEFAULT false,
    opened_at TIMESTAMP,
    format VARCHAR(20) DEFAULT 'text', -- text, audio
    UNIQUE(user_id, digest_date)
);

CREATE INDEX idx_digests_user ON user_digests(user_id);
CREATE INDEX idx_digests_date ON user_digests(digest_date);
```

### Таблиця: catalog_channels (каталог для onboarding)

```sql
CREATE TABLE catalog_channels (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    priority INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT false,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel_id, category)
);

CREATE INDEX idx_catalog_category ON catalog_channels(category, priority DESC);
CREATE INDEX idx_catalog_featured ON catalog_channels(is_featured) WHERE is_featured = true;
```

---

## Структура проекту

```
pulse_bot/
├── .env.example              # Приклад env файлу
├── .gitignore
├── README.md
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
│
├── config/
│   ├── __init__.py
│   ├── settings.py          # Конфігурація з .env
│   └── logging_config.py    # Налаштування логування
│
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point для бота
│   │
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py         # /start handler
│   │   ├── channels.py      # /add, /channels handlers
│   │   ├── forward.py       # Forward message handler (КЛЮЧОВИЙ!)
│   │   ├── digest.py        # /summary handler
│   │   ├── settings.py      # /settings handler
│   │   ├── help.py          # /help handler
│   │   └── feedback.py      # /feedback handler
│   │
│   ├── keyboards/
│   │   ├── __init__.py
│   │   ├── inline.py        # Inline keyboards
│   │   └── reply.py         # Reply keyboards
│   │
│   ├── middlewares/
│   │   ├── __init__.py
│   │   ├── auth.py          # Перевірка користувача
│   │   └── throttling.py    # Rate limiting
│   │
│   └── utils/
│       ├── __init__.py
│       ├── validators.py    # Валідація даних
│       └── formatters.py    # Форматування повідомлень
│
├── database/
│   ├── __init__.py
│   ├── connection.py        # SQLAlchemy engine setup
│   ├── models.py            # SQLAlchemy models
│   ├── queries.py           # Database queries
│   └── migrations/          # Alembic migrations
│       └── versions/
│
├── services/
│   ├── __init__.py
│   ├── monitor.py           # Telethon channel monitoring
│   ├── clustering.py        # News clustering logic
│   ├── summarization.py     # LLM summarization
│   ├── embeddings.py        # Vector embeddings generation
│   ├── analytics.py         # Analytics calculations
│   ├── digest_generator.py  # Digest generation
│   └── catalog.py           # Channel catalog management
│
├── tasks/
│   ├── __init__.py
│   ├── celery_app.py        # Celery configuration
│   ├── monitoring.py        # Periodic channel monitoring tasks
│   ├── clustering.py        # Clustering background tasks
│   └── digests.py           # Digest generation tasks
│
├── scripts/
│   ├── init_db.py           # Ініціалізація БД
│   ├── populate_catalog.py  # Заповнення каталогу каналів
│   └── test_monitoring.py   # Тестування моніторингу
│
└── tests/
    ├── __init__.py
    ├── test_handlers.py
    ├── test_clustering.py
    └── test_digest.py
```

---

## Детальна специфікація компонентів

## 1. Bot Handlers (bot/handlers/)

### 1.1 start.py - Обробка /start

**Функціонал:**
- Реєстрація нового користувача або welcome back
- Onboarding flow для нових користувачів
- Вибір способу додавання каналів

**Код структура:**

```python
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

class OnboardingStates(StatesGroup):
    choose_method = State()
    select_categories = State()
    select_channels = State()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """
    Обробка команди /start
    
    Логіка:
    1. Перевірити чи користувач існує в БД
    2. Якщо новий - створити запис + onboarding
    3. Якщо існуючий - welcome back message
    """
    user = await get_or_create_user(message.from_user)
    
    if user.is_new:
        await start_onboarding(message, state)
    else:
        await send_welcome_back(message)

async def start_onboarding(message: Message, state: FSMContext):
    """
    Початок onboarding flow
    
    Показати:
    - Вітальне повідомлення
    - Короткий опис що робить бот
    - 3 способи додавання каналів:
      1. Каталог (швидко)
      2. Forward пост (найлегше)
      3. Посилання (якщо знаєш @username)
    """
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📚 Обрати з каталогу", callback_data="onboarding:catalog")
    keyboard.button(text="📤 Форварднути пост", callback_data="onboarding:forward")
    keyboard.button(text="🔗 Додати посиланням", callback_data="onboarding:link")
    keyboard.adjust(1)
    
    text = """
👋 Привіт! Я Pulse

💓 Допоможу тримати руку на пульсі подій

Я збираю новини з твоїх улюблених каналів,
прибираю дублікати та роблю короткий дайджест щодня.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 Давай додамо перші канали:
"""
    
    await message.answer(text, reply_markup=keyboard.as_markup())
    await state.set_state(OnboardingStates.choose_method)

@router.callback_query(F.data == "onboarding:catalog")
async def onboarding_catalog(callback: CallbackQuery, state: FSMContext):
    """
    Користувач обрав каталог
    
    Показати категорії:
    - Новини
    - Бізнес
    - Технології
    - Політика
    - тощо
    """
    await show_categories(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "onboarding:forward")
async def onboarding_forward(callback: CallbackQuery, state: FSMContext):
    """
    Користувач обрав forward
    
    Інструкція:
    1. Відкрий будь-який канал
    2. Форвардни пост мені
    3. Я автоматично додам канал
    """
    text = """
📤 Додавання через forward

Це найпростіший спосіб:

1️⃣ Відкрий будь-який Telegram канал
2️⃣ Обери будь-який пост
3️⃣ Натисни "Forward" (Поділитися)
4️⃣ Відправ мені

Я автоматично розпізнаю канал і додам його!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Спробуй зараз - форвардни пост з будь-якого
   новинного каналу на який ти підписаний
"""
    
    await callback.message.edit_text(text)
    await state.clear()
    await callback.answer()

# ... інші handlers
```

**Ключові функції для реалізації:**
- `get_or_create_user(telegram_user)` - створення/отримання користувача
- `show_categories(message, state)` - показ категорій каналів
- `send_welcome_back(message)` - повідомлення для існуючих користувачів

---

### 1.2 forward.py - Forward Handler (НАЙВАЖЛИВІШИЙ!)

**Це killer feature бота!**

**Функціонал:**
- Детект forwarded повідомлень
- Розпізнавання публічних vs приватних каналів
- Перевірка чи канал вже доданий
- Додавання каналу в БД та підписки користувача
- Підтвердження з деталями каналу

**Код структура:**

```python
from aiogram import Router, F
from aiogram.types import Message
from telethon.sync import TelegramClient
from telethon.tl.types import Channel

router = Router()

@router.message(F.forward_from_chat)
async def handle_forward(message: Message):
    """
    Обробка forwarded повідомлень
    
    Важливо:
    - Спрацьовує тільки якщо Group Privacy = OFF в BotFather
    - message.forward_from_chat містить інфо про канал
    """
    
    # Витягуємо інфо про канал з forward metadata
    forward_chat = message.forward_from_chat
    
    # Перевірка типу (має бути channel)
    if forward_chat.type != "channel":
        await message.reply(
            "❌ Це не канал\n\n"
            "Я працюю тільки з каналами, а це схоже на групу або особистий чат."
        )
        return
    
    # Витягуємо дані
    channel_id = forward_chat.id
    channel_title = forward_chat.title
    channel_username = forward_chat.username  # може бути None для приватних
    
    # Перевірка чи канал вже доданий користувачем
    user = await get_user(message.from_user.id)
    existing_subscription = await check_subscription(user.id, channel_id)
    
    if existing_subscription:
        await show_already_added_message(message, channel_title)
        return
    
    # Розділяємо логіку для публічних та приватних
    if channel_username:
        # Публічний канал - можемо моніторити
        await handle_public_channel(message, channel_id, channel_username, channel_title)
    else:
        # Приватний канал - поки не підтримуємо
        await handle_private_channel(message, channel_id, channel_title)

async def handle_public_channel(
    message: Message, 
    channel_id: int, 
    channel_username: str,
    channel_title: str
):
    """
    Обробка публічного каналу
    
    Кроки:
    1. Отримати додаткову інфо через Telethon
    2. Зберегти канал в БД (якщо новий)
    3. Показати підтвердження користувачу
    4. Після підтвердження - додати підписку
    """
    
    # Отримуємо детальну інфо через Telethon
    try:
        channel_info = await get_channel_info_telethon(channel_username)
    except Exception as e:
        await message.reply(
            f"❌ Помилка отримання інфо про канал\n\n"
            f"Можливо канал видалений або змінив username."
        )
        return
    
    # Зберігаємо/оновлюємо канал в БД
    channel = await save_or_update_channel({
        'telegram_id': channel_id,
        'username': channel_username,
        'title': channel_title,
        'description': channel_info.get('description'),
        'subscribers_count': channel_info.get('participants_count'),
        'is_public': True
    })
    
    # Показуємо підтвердження
    await show_add_confirmation(message, channel, channel_info)

async def show_add_confirmation(
    message: Message,
    channel: Channel,
    channel_info: dict
):
    """
    Показати діалог підтвердження додавання каналу
    """
    
    # Визначаємо категорію автоматично (ML або keywords)
    category = await detect_category(channel.title, channel.description)
    
    # Перевіряємо ліміти (Free = 10 каналів)
    user = await get_user(message.from_user.id)
    current_count = await get_subscriptions_count(user.id)
    limit = get_user_limit(user.subscription_tier)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="✅ Додати", 
        callback_data=f"add_channel:{channel.id}"
    )
    keyboard.button(
        text="❌ Ні, дякую", 
        callback_data="cancel_add"
    )
    keyboard.adjust(2)
    
    text = f"""
✨ Новий канал знайдено!

📢 {channel.title}
👥 {format_number(channel_info['participants_count'])} підписників
📊 ~{channel_info.get('avg_posts_per_day', '?')} постів/день
🏷️ #{category}

Додати до моніторингу?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ти зараз моніториш: {current_count}/{limit} каналів
"""
    
    if current_count >= limit:
        text += "\n⚠️ Досягнуто ліміт Free плану"
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="⭐ Upgrade до Pro", callback_data="upgrade:pro")
    
    await message.reply(text, reply_markup=keyboard.as_markup())

@router.callback_query(F.data.startswith("add_channel:"))
async def confirm_add_channel(callback: CallbackQuery):
    """
    Підтвердження додавання каналу
    """
    channel_id = int(callback.data.split(":")[1])
    user = await get_user(callback.from_user.id)
    
    # Створюємо підписку
    subscription = await create_subscription(
        user_id=user.id,
        channel_id=channel_id,
        added_method='forward'
    )
    
    channel = await get_channel(channel_id)
    
    await callback.message.edit_text(
        f"✅ Канал {channel.title} додано!\n\n"
        f"Я почав моніторинг. Перший дайджест отримаєш "
        f"сьогодні о {user.digest_time.strftime('%H:%M')}"
    )
    
    await callback.answer("✅ Канал додано!")

async def handle_private_channel(
    message: Message,
    channel_id: int,
    channel_title: str
):
    """
    Обробка приватного каналу
    
    Поки що не підтримується - показуємо повідомлення
    """
    
    text = """
⚠️ Це приватний канал

На жаль, я поки не можу автоматично моніторити 
приватні канали.

Цей функціонал буде доступний в Pro версії.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Поки що можеш:
• Додавати публічні канали
• Форвардити цікаві пости вручну

[Дізнатися про Pro] [Додати інший канал]
"""
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="ℹ️ Про Pro версію", callback_data="info:pro")
    keyboard.button(text="➕ Додати інший канал", callback_data="onboarding:forward")
    keyboard.adjust(1)
    
    await message.reply(text, reply_markup=keyboard.as_markup())

async def get_channel_info_telethon(username: str) -> dict:
    """
    Отримати детальну інфо про канал через Telethon
    
    Returns:
        dict з полями:
        - participants_count
        - description
        - avg_posts_per_day (розрахункове)
        - last_post_date
    """
    # Telethon клієнт має бути ініціалізований глобально
    from services.monitor import telethon_client
    
    try:
        entity = await telethon_client.get_entity(username)
        
        # Отримуємо full info
        full = await telethon_client(GetFullChannelRequest(entity))
        
        # Отримуємо останні 100 постів для розрахунку avg
        messages = await telethon_client.get_messages(entity, limit=100)
        
        # Розраховуємо середню частоту
        if len(messages) > 1:
            time_span = (messages[0].date - messages[-1].date).total_seconds()
            avg_posts_per_day = (len(messages) / time_span) * 86400
        else:
            avg_posts_per_day = 0
        
        return {
            'participants_count': full.full_chat.participants_count,
            'description': full.full_chat.about,
            'avg_posts_per_day': round(avg_posts_per_day, 1),
            'last_post_date': messages[0].date if messages else None
        }
        
    except Exception as e:
        logger.error(f"Error getting channel info for {username}: {e}")
        raise

# ... допоміжні функції
```

**Важливо:**
- Group Privacy має бути OFF в BotFather
- Telethon client має бути ініціалізований і запущений
- Обробляти всі edge cases (канал видалено, username змінено, тощо)

---

### 1.3 channels.py - Управління каналами

**Функціонал:**
- `/channels` - показ списку каналів користувача
- `/add` - додавання каналу через посилання
- Видалення каналів
- Налаштування окремих каналів

**Код структура:**

```python
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

router = Router()

@router.message(Command("channels"))
async def cmd_channels(message: Message):
    """
    Показ списку каналів користувача
    
    Групувати по категоріях
    Показувати статистику по кожному каналу
    """
    user = await get_user(message.from_user.id)
    subscriptions = await get_user_subscriptions(user.id)
    
    if not subscriptions:
        await send_no_channels_message(message)
        return
    
    # Групуємо по категоріях
    by_category = group_channels_by_category(subscriptions)
    
    # Форматуємо повідомлення
    text = f"📱 ТВОЇ КАНАЛИ ({len(subscriptions)})\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for category, channels in by_category.items():
        text += f"{get_category_emoji(category)} {category} ({len(channels)})\n\n"
        
        for channel in channels[:3]:  # Показуємо перші 3
            stats = await get_channel_stats_for_user(channel.id, user.id)
            text += f"📢 {channel.title}\n"
            text += f"   👥 {format_number(channel.subscribers_count)} підписників\n"
            text += f"   📊 {stats['posts_today']} постів сьогодні\n"
            # Inline кнопки для управління
            text += f"\n"
        
        if len(channels) > 3:
            text += f"   [Показати всі {len(channels)} →]\n"
        
        text += "\n"
    
    # Додаємо інфо про ліміти
    limit = get_user_limit(user.subscription_tier)
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += f"{user.subscription_tier.title()} план: {len(subscriptions)}/{limit} каналів\n"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="➕ Додати канал", callback_data="add:start")
    
    if user.subscription_tier == 'free':
        keyboard.button(text="⭐ Upgrade до Pro", callback_data="upgrade:pro")
    
    keyboard.adjust(1)
    
    await message.answer(text, reply_markup=keyboard.as_markup())

@router.message(Command("add"))
async def cmd_add(message: Message):
    """
    Додавання каналу через посилання
    
    Приймає:
    - @username
    - t.me/username
    - https://t.me/username
    """
    text = """
🔗 Додати канал посиланням

Відправ мені:
• @username каналу
• або повне посилання t.me/channel

Приклад:
@ukrpravda_news
або
https://t.me/ukrpravda_news

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Швидший спосіб:
Просто форвардни пост з каналу!
"""
    
    await message.answer(text)

@router.message(F.text.regexp(r'(@[\w]+|t\.me/[\w]+|https://t\.me/[\w]+)'))
async def handle_channel_link(message: Message):
    """
    Обробка посилання на канал
    
    Парсинг різних форматів:
    - @channel
    - t.me/channel
    - https://t.me/channel
    """
    
    # Витягуємо username
    text = message.text.strip()
    
    if text.startswith('@'):
        username = text[1:]
    elif 't.me/' in text:
        username = text.split('t.me/')[-1].split('?')[0]
    else:
        await message.reply("❌ Невірний формат посилання")
        return
    
    # Перевіряємо чи канал існує
    try:
        channel_info = await get_channel_info_telethon(username)
    except Exception as e:
        await message.reply(
            f"❌ Канал не знайдено\n\n"
            f"Перевір правильність username або посилання."
        )
        return
    
    # Далі та ж логіка що в forward handler
    # ...

# ... інші handlers для управління
```

---

### 1.4 digest.py - Генерація дайджестів

**Функціонал:**
- `/summary` - дайджест на запит
- Автоматична генерація щоденних дайджестів (через Celery task)
- Форматування дайджесту
- Персоналізація по каналах користувача

**Код структура:**

```python
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from services.digest_generator import DigestGenerator

router = Router()

@router.message(Command("summary"))
async def cmd_summary(message: Message):
    """
    Генерація дайджесту на запит
    
    Процес:
    1. Показати "Генерую..." з progress bar
    2. Викликати DigestGenerator
    3. Відформатувати та відправити
    """
    
    user = await get_user(message.from_user.id)
    
    # Перевірка чи є канали
    subscriptions = await get_user_subscriptions(user.id)
    if not subscriptions:
        await message.answer(
            "📭 У тебе ще немає каналів для моніторингу\n\n"
            "Додай канали щоб я міг зробити дайджест:\n\n"
            "• Форвардни пост з каналу\n"
            "• Або обери з каталогу /start"
        )
        return
    
    # Показуємо прогрес
    progress_msg = await message.answer(
        "📰 Генерую дайджест...\n\n"
        "⏳ Зачекай 10-15 секунд"
    )
    
    try:
        # Генеруємо дайджест
        generator = DigestGenerator()
        digest = await generator.generate_for_user(
            user_id=user.id,
            date=datetime.now().date()
        )
        
        if not digest.stories:
            await progress_msg.edit_text(
                "📭 Нових новин сьогодні не знайдено\n\n"
                "Можливо твої канали ще не публікували, "
                "або всі новини були вчора."
            )
            return
        
        # Форматуємо дайджест
        formatted = await format_digest(digest, user)
        
        # Відправляємо
        await progress_msg.delete()
        
        # Розбиваємо на частини якщо дуже довгий
        for part in split_message(formatted, max_length=4000):
            await message.answer(
                part,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
        
        # Зберігаємо в історію
        await save_digest_to_history(user.id, digest)
        
    except Exception as e:
        logger.error(f"Error generating digest for user {user.id}: {e}")
        await progress_msg.edit_text(
            "❌ Помилка генерації дайджесту\n\n"
            "Спробуй пізніше або звернися в підтримку /feedback"
        )

async def format_digest(digest: Digest, user: User) -> str:
    """
    Форматування дайджесту для відправки
    
    Структура:
    - Header з датою
    - Trending секція (якщо є)
    - Новини по категоріях
    - Footer з кнопками
    """
    
    text = f"📰 ДАЙДЖЕСТ за {digest.date.strftime('%d %B %Y')}\n\n"
    
    # Trending stories (status='trending')
    trending = [s for s in digest.stories if s.status == 'trending']
    if trending:
        text += "🔥 TRENDING\n\n"
        for story in trending:
            text += format_story(story, user, expanded=True)
            text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Решта по категоріях
    by_category = group_stories_by_category(
        [s for s in digest.stories if s.status != 'trending']
    )
    
    for category, stories in by_category.items():
        emoji = get_category_emoji(category)
        text += f"{emoji} {category.upper()} ({len(stories)})\n\n"
        
        for story in stories[:5]:  # Показуємо перші 5
            text += format_story(story, user, expanded=False)
            text += "\n"
        
        if len(stories) > 5:
            text += f"   [Ще {len(stories) - 5} новин →]\n"
        
        text += "\n"
    
    # Footer
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += f"Цей дайджест згенеровано з {len(digest.total_channels)} каналів\n"
    text += f"Наступний: завтра о {user.digest_time.strftime('%H:%M')}\n\n"
    text += "[Налаштування] [Додати канали]"
    
    return text

def format_story(story: Story, user: User, expanded: bool = False) -> str:
    """
    Форматування однієї новини
    
    expanded=True - повний формат з джерелами
    expanded=False - короткий формат
    """
    
    # Іконка по статусу
    if story.status == 'trending':
        icon = "🔴"
    elif story.confidence_score > 0.8:
        icon = "🔵"
    else:
        icon = "⚪"
    
    text = f"{icon} <b>{story.title}</b>\n\n"
    
    if expanded:
        text += f"{story.summary}\n\n"
    else:
        # Короткий саммарі (перші 150 символів)
        short_summary = story.summary[:150] + "..." if len(story.summary) > 150 else story.summary
        text += f"{short_summary}\n\n"
    
    # Джерела з каналів користувача
    user_sources = [
        pub for pub in story.publications 
        if pub.channel_id in user.subscribed_channel_ids
    ]
    
    text += f"📌 У твоїх каналах ({len(user_sources)} з {story.total_publications}):\n"
    
    for pub in user_sources[:3]:
        time_str = pub.published_at.strftime("%H:%M")
        text += f"• <a href='{pub.post_url}'>{pub.channel.title}</a> - {time_str}"
        
        # Позначка першоджерела
        if pub.id == story.first_publication_id:
            text += " ⚡"
        
        text += "\n"
    
    if len(user_sources) > 3:
        text += f"• [Ще {len(user_sources) - 3} канали]\n"
    
    if expanded and story.total_publications > len(user_sources):
        text += f"\n💡 Також покрито в {story.total_publications - len(user_sources)} інших каналах\n"
    
    return text

# ... інші функції
```

---

## 2. Services (services/)

### 2.1 monitor.py - Моніторинг каналів через Telethon

**Це core функціонал який збирає пости з каналів**

**Код структура:**

```python
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Message
import asyncio
from datetime import datetime, timedelta

class ChannelMonitor:
    """
    Клас для моніторингу Telegram каналів через Telethon
    
    Підхід:
    - Один Telethon client на весь бот
    - Periodic polling кожні 5-10 хвилин
    - Зберігання last_message_id для кожного каналу
    """
    
    def __init__(self, api_id: int, api_hash: str, session_name: str):
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.last_message_ids = {}  # {channel_id: last_msg_id}
        self.is_running = False
    
    async def start(self):
        """Ініціалізація та запуск клієнта"""
        await self.client.start()
        self.is_running = True
        logger.info("Telethon client started")
        
        # Завантажуємо last_message_ids з БД
        await self.load_last_message_ids()
    
    async def stop(self):
        """Зупинка клієнта"""
        self.is_running = False
        await self.client.disconnect()
        logger.info("Telethon client stopped")
    
    async def load_last_message_ids(self):
        """Завантаження останніх ID повідомлень з БД"""
        channels = await get_all_monitored_channels()
        for channel in channels:
            self.last_message_ids[channel.telegram_id] = channel.last_message_id or 0
    
    async def monitor_channels(self, channel_ids: list[int]):
        """
        Моніторинг списку каналів
        
        Args:
            channel_ids: список Telegram ID каналів
        
        Returns:
            list[dict]: список нових постів
        """
        
        new_posts = []
        
        for channel_id in channel_ids:
            try:
                posts = await self.get_new_posts(channel_id)
                if posts:
                    new_posts.extend(posts)
                    logger.info(f"Got {len(posts)} new posts from channel {channel_id}")
                
                # Затримка щоб не перевищити rate limit
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error monitoring channel {channel_id}: {e}")
                continue
        
        return new_posts
    
    async def get_new_posts(self, channel_id: int) -> list[dict]:
        """
        Отримання нових постів з каналу
        
        Returns:
            list з dict-ами постів
        """
        
        last_id = self.last_message_ids.get(channel_id, 0)
        
        try:
            # Отримуємо канал
            channel = await self.client.get_entity(channel_id)
            
            # Отримуємо нові повідомлення
            messages = await self.client.get_messages(
                channel,
                min_id=last_id,
                limit=100  # максимум 100 нових постів за раз
            )
            
            if not messages:
                return []
            
            # Оновлюємо last_message_id
            new_last_id = messages[0].id
            self.last_message_ids[channel_id] = new_last_id
            await update_channel_last_message_id(channel_id, new_last_id)
            
            # Конвертуємо в dict для БД
            posts = []
            for msg in messages:
                if not msg.message:  # Пропускаємо service messages
                    continue
                
                post_data = await self.parse_message(msg, channel_id)
                posts.append(post_data)
            
            return posts
            
        except Exception as e:
            logger.error(f"Error getting posts from {channel_id}: {e}")
            return []
    
    async def parse_message(self, message: Message, channel_id: int) -> dict:
        """
        Парсинг Telegram повідомлення в dict для БД
        
        Returns:
            dict з полями для story_publications
        """
        
        # Підрахунок реакцій
        reactions_count = 0
        if message.reactions:
            reactions_count = sum(r.count for r in message.reactions.results)
        
        # Витягування media URLs
        media_urls = []
        has_media = False
        
        if message.media:
            has_media = True
            if message.photo:
                # Фото
                media_urls.append(f"photo:{message.photo.id}")
            elif message.video:
                # Відео
                media_urls.append(f"video:{message.video.id}")
            elif message.document:
                # Документ/GIF
                media_urls.append(f"document:{message.document.id}")
        
        # Формуємо URL поста
        channel = await self.client.get_entity(channel_id)
        if channel.username:
            post_url = f"https://t.me/{channel.username}/{message.id}"
        else:
            # Приватний канал - зберігаємо channel_id
            post_url = f"https://t.me/c/{str(channel_id)[4:]}/{message.id}"
        
        return {
            'channel_id': channel_id,
            'post_id': message.id,
            'post_url': post_url,
            'original_text': message.message,
            'published_at': message.date,
            'reactions_count': reactions_count,
            'views_count': message.views or 0,
            'forwards_count': message.forwards or 0,
            'word_count': len(message.message.split()),
            'has_media': has_media,
            'media_urls': media_urls
        }
    
    async def get_channel_info(self, username: str) -> dict:
        """
        Отримання детальної інфо про канал
        
        Використовується при додаванні нового каналу
        """
        
        entity = await self.client.get_entity(username)
        
        # Отримуємо full info
        from telethon.tl.functions.channels import GetFullChannelRequest
        full = await self.client(GetFullChannelRequest(entity))
        
        # Отримуємо останні пости для статистики
        messages = await self.client.get_messages(entity, limit=100)
        
        # Розраховуємо середню частоту публікацій
        avg_posts_per_day = 0
        if len(messages) > 1:
            time_span = (messages[0].date - messages[-1].date).total_seconds()
            if time_span > 0:
                avg_posts_per_day = (len(messages) / time_span) * 86400
        
        return {
            'telegram_id': entity.id,
            'username': entity.username,
            'title': entity.title,
            'description': full.full_chat.about,
            'participants_count': full.full_chat.participants_count,
            'avg_post_frequency': round(avg_posts_per_day, 2),
            'last_post_date': messages[0].date if messages else None
        }

# Глобальний instance
telethon_client = None

async def init_telethon_client():
    """Ініціалізація глобального Telethon client"""
    global telethon_client
    
    api_id = settings.TELETHON_API_ID
    api_hash = settings.TELETHON_API_HASH
    session_name = settings.TELETHON_SESSION_NAME
    
    telethon_client = ChannelMonitor(api_id, api_hash, session_name)
    await telethon_client.start()
    
    return telethon_client

async def get_telethon_client() -> ChannelMonitor:
    """Отримання глобального client"""
    global telethon_client
    if not telethon_client:
        telethon_client = await init_telethon_client()
    return telethon_client
```

---

### 2.2 clustering.py - Кластеризація новин

**Логіка об'єднання схожих постів в одну новину**

**Код структура:**

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta

class NewsClustering:
    """
    Кластеризація постів в новини
    
    Підхід:
    1. Для кожного нового поста генеруємо embedding
    2. Порівнюємо з існуючими новинами за останні 24 год
    3. Якщо similarity > threshold → додаємо до існуючої
    4. Якщо ні → створюємо нову новину
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
    
    async def process_new_post(self, post_data: dict) -> int:
        """
        Обробка нового поста
        
        Args:
            post_data: dict з даними поста
        
        Returns:
            story_id: ID новини до якої додано пост
        """
        
        # 1. Генеруємо embedding для поста
        from services.embeddings import generate_embedding
        embedding = await generate_embedding(post_data['original_text'])
        
        # 2. Зберігаємо пост в БД
        publication = await save_publication({
            **post_data,
            'embedding_vector': embedding
        })
        
        # 3. Шукаємо схожі новини
        story = await self.find_matching_story(embedding, post_data['published_at'])
        
        if story:
            # Додаємо до існуючої новини
            await add_publication_to_story(publication.id, story.id)
            
            # Оновлюємо статус новини (pending → verified якщо 2+ джерела)
            await update_story_status(story.id)
            
            return story.id
        else:
            # Створюємо нову новину
            story = await create_new_story(publication)
            return story.id
    
    async def find_matching_story(
        self, 
        embedding: np.ndarray, 
        published_at: datetime
    ) -> Story | None:
        """
        Пошук схожої новини
        
        Шукаємо серед новин за останні 24 години
        """
        
        # Отримуємо recent stories
        time_window = published_at - timedelta(hours=24)
        recent_stories = await get_stories_since(
            time_window, 
            statuses=['pending', 'verified', 'trending']
        )
        
        if not recent_stories:
            return None
        
        # Порівнюємо embeddings
        best_match = None
        best_similarity = 0.0
        
        for story in recent_stories:
            # Беремо середній embedding всіх публікацій новини
            story_embedding = await get_story_average_embedding(story.id)
            
            # Cosine similarity
            similarity = cosine_similarity(
                [embedding],
                [story_embedding]
            )[0][0]
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = story
        
        # Повертаємо якщо similarity > threshold
        if best_similarity >= self.threshold:
            logger.info(
                f"Found matching story {best_match.id} "
                f"with similarity {best_similarity:.3f}"
            )
            return best_match
        
        return None

async def get_story_average_embedding(story_id: int) -> np.ndarray:
    """
    Отримання середнього embedding для новини
    
    Беремо всі публікації новини і усереднюємо їх embeddings
    """
    publications = await get_story_publications(story_id)
    
    embeddings = [pub.embedding_vector for pub in publications]
    
    if not embeddings:
        return np.zeros(1536)  # OpenAI embedding size
    
    return np.mean(embeddings, axis=0)

async def create_new_story(publication: Publication) -> Story:
    """
    Створення нової новини з першої публікації
    
    Args:
        publication: перша публікація новини
    
    Returns:
        Story instance
    """
    
    # Генеруємо тимчасовий title (перші 100 символів)
    title = publication.original_text[:100] + "..." if len(publication.original_text) > 100 else publication.original_text
    
    # Визначаємо категорію
    from services.categorization import detect_category
    category = await detect_category(publication.original_text)
    
    story = await Story.create(
        title=title,
        category=category,
        first_seen_at=publication.published_at,
        status='pending',  # 1 джерело = pending
        confidence_score=0.3,
        embedding_vector=publication.embedding_vector
    )
    
    # Прив'язуємо публікацію
    await add_publication_to_story(publication.id, story.id)
    
    # Створюємо analytics запис
    await create_story_analytics(story.id, publication)
    
    logger.info(f"Created new story {story.id} from publication {publication.id}")
    
    return story

async def update_story_status(story_id: int):
    """
    Оновлення статусу новини на основі кількості джерел
    
    Логіка:
    - 1 джерело: pending
    - 2+ джерела: verified
    - 5+ джерел за годину: trending
    """
    
    story = await get_story(story_id)
    publications = await get_story_publications(story_id)
    
    sources_count = len(set(pub.channel_id for pub in publications))
    
    # Визначаємо новий статус
    if sources_count == 1:
        new_status = 'pending'
        confidence = 0.3
    elif sources_count == 2:
        new_status = 'verified'
        confidence = 0.6
    elif sources_count >= 5:
        # Перевіряємо швидкість поширення
        time_span = (publications[-1].published_at - publications[0].published_at).total_seconds()
        
        if time_span < 3600:  # Менше години
            new_status = 'trending'
            confidence = 1.0
        else:
            new_status = 'verified'
            confidence = 0.9
    else:
        new_status = 'verified'
        confidence = 0.7 + (sources_count * 0.05)
    
    # Додаткові фактори для confidence
    confidence = await calculate_confidence_score(story, publications, confidence)
    
    # Оновлюємо
    await update_story(story_id, {
        'status': new_status,
        'confidence_score': min(confidence, 1.0),
        'last_updated_at': datetime.now()
    })
    
    # Якщо статус змінився на verified - генеруємо summary
    if story.status == 'pending' and new_status == 'verified':
        from tasks.clustering import generate_story_summary
        generate_story_summary.delay(story_id)
    
    # Якщо trending - можемо відправити push notification
    if new_status == 'trending':
        from tasks.notifications import notify_trending_story
        notify_trending_story.delay(story_id)

async def calculate_confidence_score(
    story: Story,
    publications: list[Publication],
    base_score: float
) -> float:
    """
    Розрахунок фінального confidence score
    
    Враховуємо:
    - Кількість джерел (base_score)
    - Credibility джерел
    - Швидкість підтвердження
    - Час з моменту створення
    """
    
    score = base_score
    
    # Бонус за credibility джерел
    channels = await get_channels([pub.channel_id for pub in publications])
    avg_credibility = np.mean([ch.credibility_score for ch in channels])
    
    if avg_credibility > 0.8:
        score += 0.1
    elif avg_credibility < 0.5:
        score -= 0.1
    
    # Бонус за швидке підтвердження
    if len(publications) >= 2:
        confirmation_time = (publications[1].published_at - publications[0].published_at).total_seconds()
        
        if confirmation_time < 1800:  # Менше 30 хв
            score += 0.1
        elif confirmation_time < 3600:  # Менше години
            score += 0.05
    
    # Штраф за затримку без підтвердження
    age_hours = (datetime.now() - story.first_seen_at).total_seconds() / 3600
    
    if len(publications) == 1 and age_hours > 24:
        score -= 0.2
    
    return score
```

---

### 2.3 summarization.py - Резюмування через LLM

**Генерація саммарі для новин через Claude API**

**Код структура:**

```python
from anthropic import Anthropic
import asyncio

class NewsSummarization:
    """
    Резюмування новин через Claude API
    """
    
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-haiku-20240307"  # Haiku для MVP
    
    async def summarize_story(self, story_id: int) -> str:
        """
        Створення резюме для новини
        
        Args:
            story_id: ID новини
        
        Returns:
            str: згенерований summary
        """
        
        # Отримуємо всі публікації новини
        publications = await get_story_publications(story_id)
        
        if not publications:
            raise ValueError(f"No publications found for story {story_id}")
        
        # Формуємо промпт
        prompt = self._build_summary_prompt(publications)
        
        # Викликаємо Claude
        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            summary = response.content[0].text
            
            # Генеруємо title (перше речення summary)
            title = self._extract_title(summary)
            
            # Оновлюємо story
            await update_story(story_id, {
                'summary': summary,
                'title': title
            })
            
            logger.info(f"Generated summary for story {story_id}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary for story {story_id}: {e}")
            raise
    
    def _build_summary_prompt(self, publications: list[Publication]) -> str:
        """
        Формування промпта для Claude
        
        Оптимізуємо кількість токенів:
        - Беремо ключові фрази з кожної публікації
        - Обмежуємо довжину
        """
        
        # Сортуємо по часу
        pubs_sorted = sorted(publications, key=lambda p: p.published_at)
        
        # Формуємо контекст
        context = "Наступні тексти описують одну новину з різних джерел:\n\n"
        
        for i, pub in enumerate(pubs_sorted, 1):
            # Беремо перші 300 слів з кожного
            text = ' '.join(pub.original_text.split()[:300])
            channel_name = pub.channel.title
            time = pub.published_at.strftime("%H:%M")
            
            context += f"Джерело {i} ({channel_name}, {time}):\n{text}\n\n"
        
        # Інструкції
        prompt = f"""{context}

Завдання: створи короткий, інформативний summary цієї новини українською мовою.

Вимоги:
- Довжина: 150-250 слів
- Стиль: нейтральний, журналістський
- Включи: основні факти, цифри, імена, контекст
- Не включай: оціночні судження, своє ставлення
- Перше речення має бути заголовком (50-80 символів)

Summary:"""
        
        return prompt
    
    def _extract_title(self, summary: str) -> str:
        """
        Витягування title з summary
        
        Беремо перше речення
        """
        sentences = summary.split('.')
        if sentences:
            title = sentences[0].strip()
            # Обрізаємо якщо дуже довгий
            if len(title) > 100:
                title = title[:97] + "..."
            return title
        return summary[:100]
    
    async def summarize_digest(
        self, 
        stories: list[Story], 
        user_context: dict
    ) -> str:
        """
        Резюмування дайджесту для користувача
        
        Опційно: можна додати персоналізацію
        на основі інтересів користувача
        """
        # Для майбутньої персоналізації
        pass
```

---

## 3. Celery Tasks (tasks/)

### 3.1 monitoring.py - Періодичний моніторинг

**Background task який запускається кожні 5-10 хвилин**

**Код структура:**

```python
from celery import Celery
from celery.schedules import crontab
import asyncio

celery_app = Celery('pulse')

@celery_app.task(name='tasks.monitor_all_channels')
def monitor_all_channels():
    """
    Періодичний моніторинг всіх активних каналів
    
    Запускається кожні 5 хвилин
    """
    asyncio.run(async_monitor_all_channels())

async def async_monitor_all_channels():
    """
    Async логіка моніторингу
    """
    from services.monitor import get_telethon_client
    
    # Отримуємо список всіх каналів для моніторингу
    channels = await get_all_active_channels()
    channel_ids = [ch.telegram_id for ch in channels]
    
    logger.info(f"Starting monitoring of {len(channel_ids)} channels")
    
    # Моніторимо
    monitor = await get_telethon_client()
    new_posts = await monitor.monitor_channels(channel_ids)
    
    logger.info(f"Collected {len(new_posts)} new posts")
    
    # Обробляємо кожен пост
    from services.clustering import NewsClustering
    clustering = NewsClustering()
    
    for post_data in new_posts:
        try:
            # Запускаємо кластеризацію для кожного поста
            story_id = await clustering.process_new_post(post_data)
            logger.debug(f"Post {post_data['post_id']} added to story {story_id}")
        except Exception as e:
            logger.error(f"Error processing post {post_data.get('post_id')}: {e}")
            continue
    
    return len(new_posts)

@celery_app.task(name='tasks.cleanup_old_stories')
def cleanup_old_stories():
    """
    Архівування старих новин
    
    Запускається щодня о 03:00
    """
    asyncio.run(async_cleanup_old_stories())

async def async_cleanup_old_stories():
    """
    Переміщення старих новин в статус archived
    """
    from datetime import datetime, timedelta
    
    # Новини старіше 48 годин → archived
    threshold = datetime.now() - timedelta(hours=48)
    
    old_stories = await get_stories_before(
        threshold, 
        statuses=['pending', 'verified', 'trending']
    )
    
    count = 0
    for story in old_stories:
        await update_story(story.id, {'status': 'archived'})
        count += 1
    
    logger.info(f"Archived {count} old stories")
    
    return count
```

---

### 3.2 digests.py - Генерація дайджестів

**Background task для автоматичних дайджестів**

**Код структура:**

```python
from celery import Celery
from datetime import datetime, time
import asyncio

@celery_app.task(name='tasks.generate_scheduled_digests')
def generate_scheduled_digests(hour: int):
    """
    Генерація дайджестів для користувачів з заданим часом
    
    Викликається щогодини (через crontab)
    """
    asyncio.run(async_generate_scheduled_digests(hour))

async def async_generate_scheduled_digests(hour: int):
    """
    Генерація та відправка дайджестів
    """
    from services.digest_generator import DigestGenerator
    from bot.main import bot
    
    # Знаходимо користувачів у яких час дайджесту = hour
    users = await get_users_with_digest_time(hour)
    
    logger.info(f"Generating digests for {len(users)} users at {hour}:00")
    
    generator = DigestGenerator()
    
    for user in users:
        try:
            # Генеруємо дайджест
            digest = await generator.generate_for_user(
                user_id=user.id,
                date=datetime.now().date()
            )
            
            if not digest.stories:
                # Немає новин - пропускаємо
                continue
            
            # Форматуємо
            from bot.handlers.digest import format_digest
            formatted = await format_digest(digest, user)
            
            # Відправляємо користувачу
            await bot.send_message(
                chat_id=user.telegram_id,
                text=formatted,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            
            # Зберігаємо в історію
            await save_digest_to_history(user.id, digest)
            
            logger.info(f"Sent digest to user {user.id}")
            
        except Exception as e:
            logger.error(f"Error generating digest for user {user.id}: {e}")
            continue
    
    return len(users)

# Налаштування розкладу
celery_app.conf.beat_schedule = {
    'monitor-channels-every-5-min': {
        'task': 'tasks.monitor_all_channels',
        'schedule': 300.0,  # 5 хвилин
    },
    'cleanup-old-stories-daily': {
        'task': 'tasks.cleanup_old_stories',
        'schedule': crontab(hour=3, minute=0),  # Щодня о 03:00
    },
    # Дайджести щогодини
    'generate-digests-00': {
        'task': 'tasks.generate_scheduled_digests',
        'schedule': crontab(hour=0, minute=0),
        'args': (0,)
    },
    'generate-digests-01': {
        'task': 'tasks.generate_scheduled_digests',
        'schedule': crontab(hour=1, minute=0),
        'args': (1,)
    },
    # ... для кожної години до 23
}
```

---

## 4. Configuration і Environment

### .env.example

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Telethon (для моніторингу каналів)
TELETHON_API_ID=your_api_id
TELETHON_API_HASH=your_api_hash
TELETHON_SESSION_NAME=pulse_monitor

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/pulse_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Claude API
ANTHROPIC_API_KEY=your_anthropic_api_key

# OpenAI (для embeddings)
OPENAI_API_KEY=your_openai_api_key

# Logging
LOG_LEVEL=INFO

# Limits
FREE_TIER_CHANNEL_LIMIT=10
PRO_TIER_CHANNEL_LIMIT=50
```

### config/settings.py

```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELETHON_API_ID: int
    TELETHON_API_HASH: str
    TELETHON_SESSION_NAME: str = "pulse_monitor"
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # APIs
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str
    
    # Clustering
    SIMILARITY_THRESHOLD: float = 0.85
    
    # Limits
    FREE_TIER_CHANNEL_LIMIT: int = 10
    PRO_TIER_CHANNEL_LIMIT: int = 50
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

---

## 5. Docker Setup

### docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: pulse_db
      POSTGRES_USER: pulse_user
      POSTGRES_PASSWORD: pulse_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
  
  bot:
    build: .
    command: python -m bot.main
    depends_on:
      - postgres
      - redis
    env_file:
      - .env
    restart: unless-stopped
  
  celery_worker:
    build: .
    command: celery -A tasks.celery_app worker --loglevel=info
    depends_on:
      - postgres
      - redis
    env_file:
      - .env
    restart: unless-stopped
  
  celery_beat:
    build: .
    command: celery -A tasks.celery_app beat --loglevel=info
    depends_on:
      - postgres
      - redis
    env_file:
      - .env
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run
CMD ["python", "-m", "bot.main"]
```

---

## 6. Testing Strategy

### tests/test_clustering.py

```python
import pytest
from services.clustering import NewsClustering

@pytest.mark.asyncio
async def test_similar_posts_clustered():
    """
    Тест що схожі пости об'єднуються в одну новину
    """
    clustering = NewsClustering(similarity_threshold=0.85)
    
    # Створюємо два схожі пости
    post1 = {
        'original_text': 'Уряд оголосив нову економічну реформу...',
        'channel_id': 1,
        'published_at': datetime.now()
    }
    
    post2 = {
        'original_text': 'Новий економічний план від уряду...',
        'channel_id': 2,
        'published_at': datetime.now()
    }
    
    # Обробляємо
    story_id_1 = await clustering.process_new_post(post1)
    story_id_2 = await clustering.process_new_post(post2)
    
    # Мають бути в одній новині
    assert story_id_1 == story_id_2

@pytest.mark.asyncio
async def test_different_posts_separate():
    """
    Тест що різні пости створюють окремі новини
    """
    # ...
```

---

## 7. Deployment Checklist

### Перед запуском в production:

**Infrastructure:**
- [ ] PostgreSQL з pgvector встановлено
- [ ] Redis запущено
- [ ] Celery workers працюють
- [ ] Celery beat запущено

**Configuration:**
- [ ] .env файл заповнено всіма ключами
- [ ] TELEGRAM_BOT_TOKEN отримано з BotFather
- [ ] TELETHON_API_ID/API_HASH отримано з my.telegram.org
- [ ] ANTHROPIC_API_KEY валідний
- [ ] OPENAI_API_KEY валідний
- [ ] DATABASE_URL правильний

**Database:**
- [ ] Migrations запущено
- [ ] Catalog channels заповнено (50-100 каналів)
- [ ] Indexes створено

**Monitoring:**
- [ ] Logging налаштовано
- [ ] Error tracking (Sentry?)
- [ ] Metrics (Prometheus?)

**Security:**
- [ ] .env в .gitignore
- [ ] API keys не в коді
- [ ] Database credentials безпечні
- [ ] Rate limiting налаштовано

**Testing:**
- [ ] Unit tests пройдено
- [ ] Integration tests пройдено
- [ ] Manual testing виконано

---

## 8. Performance Optimization

### Важливі оптимізації:

**Database:**
- Indexes на всіх foreign keys
- Vector indexes для similarity search
- Connection pooling (SQLAlchemy)
- Read replicas для analytics queries

**Caching:**
- Redis для session storage
- Cache frequently accessed channels
- Cache embeddings

**Rate Limiting:**
- Telethon: 20 req/sec max
- Claude API: according to tier
- User actions: 10 req/min per user

**Background Processing:**
- Clustering асинхронно через Celery
- Summarization асинхронно
- Digest generation batch processing

---

## 9. Monitoring & Debugging

### Логування:

```python
import logging

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### Key metrics to track:

- **Bot metrics:**
  - Active users (DAU/MAU)
  - Messages processed
  - Errors per handler

- **Monitoring metrics:**
  - Channels monitored
  - Posts collected per hour
  - Clustering accuracy
  - LLM API latency

- **System metrics:**
  - Database connections
  - Redis memory usage
  - Celery queue size
  - API response times

---

## 10. Next Steps After MVP

**Фаза 2 (місяці 4-6):**
- [ ] Audio digests (TTS)
- [ ] Advanced analytics
- [ ] Dashboard для каналів
- [ ] Improved categorization

**Фаза 3 (місяці 7-9):**
- [ ] Partnership program
- [ ] Paid tiers
- [ ] Private channels support
- [ ] Groups support

**Фаза 4 (місяці 10+):**
- [ ] API access
- [ ] White-label solution
- [ ] Multi-language
- [ ] Web dashboard

---

## Contact & Support

**Якщо виникнуть питання під час розробки:**

1. Перевірте документацію бібліотек:
   - aiogram: https://docs.aiogram.dev/
   - Telethon: https://docs.telethon.dev/
   - Anthropic: https://docs.anthropic.com/

2. Common issues:
   - Telethon session issues → видаліть .session файл і ре-авторизуйтесь
   - pgvector not found → встановіть extension: `CREATE EXTENSION vector;`
   - Rate limits → додайте delays між запитами

3. Performance issues:
   - Slow clustering → оптимізуйте vector indexes
   - Slow summarization → використовуйте Haiku замість Sonnet
   - Database slow → додайте indexes

---

**Успіхів у розробці! 🚀**

Це детальне ТЗ покриває всі ключові аспекти MVP. 
Розробник має всю необхідну інформацію для початку роботи.
