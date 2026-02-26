from typing import Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, UserSubscription
from datetime import datetime, timezone
from loguru import logger

# Конфігурація лімітів для різних планів
SUBSCRIPTION_LIMITS = {
    "demo": 3,
    "basic": 6,
    "standard": 10,
    "premium": 15
}

class SubscriptionService:
    """Сервіс для керування лімітами та статусами підписок"""

    @staticmethod
    async def get_user_status(user_id: int, session: AsyncSession) -> Dict[str, Any]:
        """
        Отримати детальний статус підписки користувача.
        """
        # 1. Отримуємо дані користувача
        user_res = await session.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one_or_none()
        
        if not user:
            # Якщо користувача немає в базі, він вважається демо-користувачем
            tier = "demo"
            expires_at = None
        else:
            tier = user.subscription_tier or "demo"
            expires_at = user.subscription_expires_at
            
            # Перевірка на прострочення підписки
            if expires_at and expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                tier = "demo"

        # 2. Підраховуємо поточну кількість підписок
        count_res = await session.execute(
            select(func.count(UserSubscription.id)).where(UserSubscription.user_id == user_id)
        )
        sub_count = count_res.scalar() or 0
        
        limit = SUBSCRIPTION_LIMITS.get(tier, 3)
        
        return {
            "tier": tier,
            "sub_count": sub_count,
            "limit": limit,
            "can_add": sub_count < limit,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "is_active": user.is_active if user else True
        }

    @staticmethod
    async def check_limit_before_add(user_id: int, session: AsyncSession) -> bool:
        """
        Швидка перевірка можливості додавання нового каналу.
        """
        status = await SubscriptionService.get_user_status(user_id, session)
        return status["can_add"]

subscription_service = SubscriptionService()
