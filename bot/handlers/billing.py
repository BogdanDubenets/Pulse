from aiogram import Router, F, types
from aiogram.types import PreCheckoutQuery, SuccessfulPayment
from sqlalchemy import select, update
from database.connection import AsyncSessionLocal
from database.models import User
from datetime import datetime, timedelta, timezone
from loguru import logger

router = Router()

@router.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """
    Telegram запитує підтвердження перед оплатою.
    Тут можна перевірити наявність товару, але для Stars зазвичай просто 'ok'.
    """
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def on_successful_payment(message: types.Message):
    """
    Обробка успішного платежу. Це повідомлення приходить ВІД Telegram БОТУ,
    коли користувач оплатив інвойс у Mini App.
    """
    payment = message.successful_payment
    payload = payment.invoice_payload # Наприклад: "sub_premium_461874849"
    
    logger.info(f"💰 Successful payment received: {payload}")
    
    parts = payload.split("_")
    if len(parts) >= 3 and parts[0] == "sub":
        tier = parts[1]
        user_id = int(parts[2])
        
        async with AsyncSessionLocal() as session:
            # Оновлюємо статус користувача
            now = datetime.now(timezone.utc)
            # За замовчуванням +30 днів
            expires_at = now + timedelta(days=30)
            
            # TODO: Тут можна додати логіку бонусних днів, 
            # якщо перехід був Upgrade. Але для MVP — просто оновлюємо план.
            
            stmt = update(User).where(User.id == user_id).values(
                subscription_tier=tier,
                subscription_expires_at=expires_at
            )
            await session.execute(stmt)
            await session.commit()
            
            logger.info(f"✅ User {user_id} upgraded to {tier} until {expires_at}")
            
            await message.answer(
                f"🎉 <b>Дякуємо за підписку!</b>\n\n"
                f"Ваш план оновлено до <b>{tier.capitalize()}</b>.\n"
                f"Тепер у вас більше слотів для каналів та доступ до преміум-функцій Pulse. ✨"
            )
