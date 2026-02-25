from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import User
from config.settings import config
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/affiliate", tags=["affiliate"])

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

class AffiliateStats(BaseModel):
    user_id: int
    referral_link: str
    earned_stars: float
    referrals_count: int
    commission_percent: int

@router.get("/stats/{user_id}", response_model=AffiliateStats)
async def get_affiliate_stats(user_id: int, db: AsyncSession = Depends(get_db)):
    """Отримати статистику партнерської програми для користувача"""
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")
    
    # Припускаємо, що юзернейм бота знаємо або беремо з конфігу
    bot_username = "pulse_daily_bot" # Оновлено згідно зі скріншотом
    ref_link = f"https://t.me/{bot_username}?start=aff_{user_id}"
    
    return AffiliateStats(
        user_id=user_id,
        referral_link=ref_link,
        earned_stars=user.affiliate_earned_stars,
        referrals_count=user.referrals_count,
        commission_percent=10 # Оновлено до 10% згідно зі скріншотом
    )
