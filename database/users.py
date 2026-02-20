from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from database.connection import AsyncSessionLocal
from database.models import User
from loguru import logger
from datetime import datetime, timezone

async def upsert_user(user_id: int, first_name: str = None, username: str = None, language_code: str = "uk"):
    """
    Створює або оновлює дані користувача в базі даних.
    """
    try:
        async with AsyncSessionLocal() as session:
            # Використовуємо ON CONFLICT для PostgreSQL для атомарного upsert
            stmt = insert(User).values(
                id=user_id,
                first_name=first_name,
                username=username,
                language_code=language_code,
                created_at=datetime.now(timezone.utc)
            ).on_conflict_do_update(
                index_elements=[User.id],
                set_={
                    "first_name": first_name,
                    "username": username,
                    "language_code": language_code
                }
            )
            
            logger.debug(f"Executing upsert for user {user_id} (stmt prepared)")
            await session.execute(stmt)
            await session.commit()
            logger.info(f"✅ Користувач {user_id} ({first_name}) успішно зареєстрований/оновлений у БД.")
            return True
            
    except Exception as e:
        logger.error(f"❌ Помилка при реєстрації користувача {user_id}: {e}")
        return False
