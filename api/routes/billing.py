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
    tier: str # basic, standard, premium

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
    if req.tier not in TIER_PRICES:
        raise HTTPException(status_code=400, detail="Invalid tier")
    
    price = TIER_PRICES[req.tier]
    
    # Використовуємо Bot API для генерації посилання
    bot = Bot(token=config.BOT_TOKEN.get_secret_value())
    
    try:
        # У Telegram Stars currency завжди "XTR"
        # payload - це дані, які повернуться в вебхуку
        invoice_link = await bot.create_invoice_link(
            title=f"Pulse {req.tier.capitalize()} Subscription",
            description=f"Щомісячна підписка на Pulse ({req.tier} рівень)",
            payload=f"sub_{req.tier}_{req.user_id}",
            provider_token="", # Для Stars токен провайдера порожній
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
