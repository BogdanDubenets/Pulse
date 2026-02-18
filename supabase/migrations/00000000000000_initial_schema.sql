-- Схема бази даних проекту Pulse (версія 1.0)
-- Розроблено згідно з дорожньою картою Antigravity

-- Активація розширення для векторних обчислень (для кластеризації новин)
CREATE EXTENSION IF NOT EXISTS vector;

-- Таблиця каналів (Джерела інформації)
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    title TEXT NOT NULL,
    category TEXT,
    credibility_score FLOAT DEFAULT 0.5, -- 0.0 до 1.0
    is_active BOOLEAN DEFAULT TRUE,
    last_scanned_at TIMESTAMP WITH TIME ZONE,
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
    confidence_score FLOAT DEFAULT 0.0, -- Розраховується на основі джерел
    status TEXT DEFAULT 'pending', -- pending, verified, trending, archived
    embedding_vector VECTOR(1536) -- Для OpenAI Embeddings (1536 вимірів)
);

-- Таблиця публікацій (Конкретні пости в каналах)
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

-- Таблиця підписок користувачів (Для персоналізованих дайджестів)
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL, -- Telegram User ID
    channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, channel_id)
);

-- Таблиця аналітики історій
CREATE TABLE IF NOT EXISTS story_analytics (
    id SERIAL PRIMARY KEY,
    story_id INTEGER REFERENCES stories(id) ON DELETE CASCADE,
    spread_speed FLOAT, -- Канали на годину
    total_reach INTEGER DEFAULT 0,
    engagement_rate FLOAT DEFAULT 0.0,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Індекси для швидкого пошуку
CREATE INDEX IF NOT EXISTS idx_stories_status ON stories(status);
CREATE INDEX IF NOT EXISTS idx_publications_story ON publications(story_id);
CREATE INDEX IF NOT EXISTS idx_publications_published_at ON publications(published_at);
