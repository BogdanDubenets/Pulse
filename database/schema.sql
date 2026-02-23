-- Схема бази даних проекту Pulse (версія 2.0)
-- Оновлено для підтримки 3-рівневої системи слотів та особистих кабінетів

-- Активація розширення для векторних обчислень
CREATE EXTENSION IF NOT EXISTS vector;

-- Таблиця каналів (Джерела інформації)
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    title TEXT NOT NULL,
    category TEXT,
    credibility_score FLOAT DEFAULT 0.5,
    is_active BOOLEAN DEFAULT TRUE,
    is_core BOOLEAN DEFAULT FALSE,
    partner_status TEXT DEFAULT 'organic', -- premium, pinned, organic
    partner_expires_at TIMESTAMP WITH TIME ZONE,
    pinned_msg_id BIGINT,
    posts_count_24h INTEGER DEFAULT 0,
    avatar_url TEXT,
    last_scanned_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблиця користувачів
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY, -- Telegram User ID
    first_name TEXT,
    username TEXT,
    language_code TEXT DEFAULT 'uk',
    morning_digest_time TEXT DEFAULT '08:00',
    evening_digest_time TEXT DEFAULT '20:00',
    is_active BOOLEAN DEFAULT TRUE,
    subscription_tier TEXT DEFAULT 'demo',
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблиця історій (Кластеризовані новини)
CREATE TABLE IF NOT EXISTS stories (
    id SERIAL PRIMARY KEY,
    title TEXT,
    summary TEXT,
    category TEXT,
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    confidence_score FLOAT DEFAULT 0.0,
    status TEXT DEFAULT 'pending',
    embedding_vector VECTOR(768) -- Оновлено до 768 для Gemini
);

-- Таблиця публікацій
CREATE TABLE IF NOT EXISTS publications (
    id SERIAL PRIMARY KEY,
    story_id INTEGER REFERENCES stories(id) ON DELETE CASCADE,
    channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
    telegram_message_id BIGINT NOT NULL,
    content TEXT,
    url TEXT,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    views INTEGER DEFAULT 0,
    reactions INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel_id, telegram_message_id)
);

-- Таблиця підписок користувачів
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
    position INTEGER DEFAULT 0,
    last_changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, channel_id)
);

-- Таблиця аукціонів
CREATE TABLE IF NOT EXISTS auctions (
    id SERIAL PRIMARY KEY,
    category TEXT,
    current_bid INTEGER DEFAULT 0, -- В зірках
    leader_user_id BIGINT,
    channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
    ends_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Індекси
CREATE INDEX IF NOT EXISTS idx_stories_status ON stories(status);
CREATE INDEX IF NOT EXISTS idx_publications_story ON publications(story_id);
CREATE INDEX IF NOT EXISTS idx_publications_published_at ON publications(published_at);
CREATE INDEX IF NOT EXISTS idx_auctions_category ON auctions(category);
