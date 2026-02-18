from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.settings import config

# Створення асинхронного engine
engine = create_async_engine(
    config.DATABASE_URL,
    echo=False,
    future=True
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
