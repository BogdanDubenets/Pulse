from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.settings import config

import ssl

# Очищення та підготовка DATABASE_URL для asyncpg
db_url = config.DATABASE_URL
connect_args = {}

if "?sslmode=require" in db_url:
    db_url = db_url.replace("?sslmode=require", "")
    # Створюємо SSL-контекст, який дозволяє підключення без суворої перевірки сертифіката
    # Це необхідно для баз даних у хмарах типу Supabase/Railway
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ctx

# Створення асинхронного engine
engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
    connect_args=connect_args
)

# Створення фабрики сесій
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
