from aiogram import Router, F, types
from aiogram.types import PreCheckoutQuery, Message
from sqlalchemy import update
from database.connection import AsyncSessionLocal
from database.models import User
from datetime import datetime, timedelta, timezone

router = Router()

@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    # У Telegram Stars ми завжди підтверджуємо PreCheckoutQuery
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    # Payload format: sub_{tier}_{user_id}
    parts = payload.split("_")
    if len(parts) < 3 or parts[0] != "sub":
        return

    tier = parts[1]
    user_id = int(parts[2])
    
    # Оновлюємо статус користувача в БД
    async with AsyncSessionLocal() as session:
        # Встановлюємо підписку на 30 днів
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                subscription_tier=tier,
                subscription_expires_at=expires_at
            )
        )
        await session.commit()

    await message.answer(
        f"✅ Оплата успішна! Ваш план оновлено до **{tier.capitalize()}**.\n"
        f"Тепер вам доступно більше можливостей у Pulse."
    )
