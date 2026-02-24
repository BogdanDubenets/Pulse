from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import User
from config.settings import config
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone
from aiogram import Bot
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# --- Pydantic Models ---

class InvoiceRequest(BaseModel):
    user_id: int
    tier: str # basic, standard, premium, ad_premium, auction_bid
    channel_id: Optional[int] = None
    days: Optional[int] = None
    category: Optional[str] = None
    amount: Optional[int] = None

class InvoiceResponse(BaseModel):
    invoice_link: str

# Ціни в Telegram Stars
TIER_PRICES = {
    "basic": 60,
    "standard": 90,
    "premium": 120
}

# Рівні планів для перевірки Up/Down Grade
TIER_LEVELS = {
    "demo": 0,
    "basic": 1,
    "standard": 2,
    "premium": 3
}

# --- Endpoints ---

@router.post("/create-invoice", response_model=InvoiceResponse)
async def create_invoice(req: InvoiceRequest, db: AsyncSession = Depends(get_db)):
    """Створити посилання на оплату через Telegram Stars"""
    price = 0
    title = ""
    description = ""
    payload = ""
    prices = []

    if req.tier in TIER_PRICES:
        target_price = TIER_PRICES[req.tier]
        target_level = TIER_LEVELS.get(req.tier, 0)
        
        # Перевіряємо поточну підписку
        user_res = await db.execute(select(User).where(User.id == req.user_id))
        user = user_res.scalar_one_or_none()
        
        current_tier = user.subscription_tier if user else "demo"
        current_level = TIER_LEVELS.get(current_tier, 0)
        
        # 1. Заборона Downgrade (але дозволяємо Upgrade та Extension)
        if target_level < current_level:
            raise HTTPException(
                status_code=400, 
                detail=f"Неможливо перейти з {current_tier} на нижчий рівень {req.tier}. Тільки Upgrade або Extension."
            )
        
        discount = 0
        is_upgrade = target_level > current_level
        is_extension = target_level == current_level
        
        if is_upgrade and user and current_tier in TIER_PRICES and user.subscription_expires_at:
            now = datetime.now(timezone.utc)
            if user.subscription_expires_at.replace(tzinfo=timezone.utc) > now:
                remaining_time = user.subscription_expires_at.replace(tzinfo=timezone.utc) - now
                remaining_days = remaining_time.days + (remaining_time.seconds / 86400)
                
                # Денна вартість поточного плану
                current_daily_price = TIER_PRICES[current_tier] / 30
                discount = int(remaining_days * current_daily_price)
        
        # Для Recurring ми завжди використовуємо ПОВНУ ціну цільового плану.
        # А різницю (знижку) ми компенсуємо бонусними днями в бот-хендлері.
        price = target_price
        
        bonus_days_msg = ""
        if is_upgrade and user and current_tier in TIER_PRICES and user.subscription_expires_at:
            now = datetime.now(timezone.utc)
            if user.subscription_expires_at.replace(tzinfo=timezone.utc) > now:
                remaining_time = user.subscription_expires_at.replace(tzinfo=timezone.utc) - now
                remaining_days = remaining_time.days + (remaining_time.seconds / 86400)
                
                # Стрічку бонусних днів ми лише показуємо для інфо, сам розрахунок буде в боті
                current_daily_price = TIER_PRICES[current_tier] / 30
                new_daily_price = target_price / 30
                bonus_days = int((remaining_days * current_daily_price) / new_daily_price)
                if bonus_days > 0:
                    bonus_days_msg = f"\n🎁 +{bonus_days} бонусних днів за перехід з {current_tier.capitalize()}"

        if is_upgrade:
            title = f"Upgrade: Pulse {req.tier.capitalize()}"
            description = (
                f"💎 Пакет: {req.tier.capitalize()} ({target_price} Stars)"
                f"{bonus_days_msg}\n"
                f"🔄 Автоподовження: кожного місяця"
            )
        else:
            title = f"Pulse {req.tier.capitalize()} Plan"
            description = (
                f"Підписка на Pulse ({req.tier} рівень)\n"
                f"🔄 Автоподовження: кожного місяця"
            )
            
        prices = [{"label": f"Pulse {req.tier.capitalize()} (30 дн.)", "amount": price}]
        payload = f"sub_{req.tier}_{req.user_id}"
    elif req.tier == "ad_premium":
        price = 1 # Тестова ціна
        title = f"Premium Slot"
        description = f"Преміум-слот для каналу на {req.days} днів"
        payload = f"ad_{req.days}_{req.channel_id}_{req.user_id}"
        prices = [{"label": "Оплата за слот", "amount": price}]
    elif req.tier == "auction_bid":
        price = req.amount or 1
        title = f"Auction Bid: {req.category}"
        description = f"Ставка за Top-1 у категорії {req.category}"
        payload = f"bid_{req.category}_{req.channel_id}_{price}_{req.user_id}"
        prices = [{"label": "Ставка в аукціоні", "amount": price}]
    else:
        raise HTTPException(status_code=400, detail="Invalid payment type")
    
    # Використовуємо Bot API для генерації посилання
    bot = Bot(token=config.BOT_TOKEN.get_secret_value())
    
    try:
        invoice_link = await bot.create_invoice_link(
            title=title,
            description=description,
            payload=payload,
            provider_token="", 
            currency="XTR",
            prices=prices,
            subscription_period=2592000 # 30 днів у секундах для Recurring
        )
        return {"invoice_link": invoice_link}
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        raise HTTPException(status_code=500, detail="Не вдалося створити інвойс")
    finally:
        await bot.session.close()

@router.post("/webhook")
async def payment_webhook(data: dict, db: AsyncSession = Depends(get_db)):
    """
    Обробка успішного платежу. 
    УВАГА: Цей ендпоінт має викликатися ботом або бути захищеним.
    """
    # Це спрощена версія. В aiogram оплата зазвичай обробляється через PreCheckoutQuery/SuccessfulMessage.
    # Якщо ми хочемо обробляти це через API, нам потрібен кастомний механізм.
    # Зазвичай краще обробляти SuccessfulPayment безпосередньо в коді бота (handlers/billing.py).
    return {"status": "ok", "message": "Webhook received"}
