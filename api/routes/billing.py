from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import User
from config.settings import config
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from aiogram import Bot

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
    "basic": 50,
    "standard": 90,
    "premium": 120
}

# --- Endpoints ---

@router.post("/create-invoice", response_model=InvoiceResponse)
async def create_invoice(req: InvoiceRequest, db: AsyncSession = Depends(get_db)):
    """Створити посилання на оплату через Telegram Stars"""
    price = 0
    title = ""
    description = ""
    payload = ""

    if req.tier in TIER_PRICES:
        price = TIER_PRICES[req.tier]
        title = f"Pulse {req.tier.capitalize()} Subscription"
        description = f"Щомісячна підписка на Pulse ({req.tier} рівень)"
        payload = f"sub_{req.tier}_{req.user_id}"
    elif req.tier == "ad_premium":
        price = 1 # Тестова ціна
        title = f"Premium Slot"
        description = f"Преміум-слот для каналу на {req.days} днів"
        payload = f"ad_{req.days}_{req.channel_id}_{req.user_id}"
    elif req.tier == "auction_bid":
        price = req.amount or 1
        title = f"Auction Bid: {req.category}"
        description = f"Ставка за Top-1 у категорії {req.category}"
        payload = f"bid_{req.category}_{req.channel_id}_{price}_{req.user_id}"
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
            prices=[{"label": "Оплата", "amount": price}]
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
