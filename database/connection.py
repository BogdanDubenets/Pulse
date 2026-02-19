from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.settings import config

import ssl

# Очищення та підготовка DATABASE_URL для asyncpg
db_url = config.DATABASE_URL
if "?sslmode=require" in db_url:
    db_url = db_url.replace("?sslmode=require", "")
    connect_args = {"ssl": True}
else:
    connect_args = {}

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
