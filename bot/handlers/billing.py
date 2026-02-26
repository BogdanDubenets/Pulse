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
    Обробка успішного платежу.
    Впроваджено перерахунок залишку днів (Proration) з заокругленням вгору.
    """
    payment = message.successful_payment
    payload = payment.invoice_payload
    
    logger.info(f"💰 Successful payment received: {payload}")
    
    parts = payload.split("_")
    if len(parts) >= 3 and parts[0] == "sub":
        tier = parts[1]
        user_id = int(parts[2])
        
        # Ціни для розрахунку (Stars/день)
        prices = {"basic": 60, "standard": 90, "premium": 120}
        
        async with AsyncSessionLocal() as session:
            # Отримуємо поточний статус
            res = await session.execute(select(User).where(User.id == user_id))
            user = res.scalar_one_or_none()
            
            if not user:
                return

            now = datetime.now(timezone.utc)
            current_expiry = user.subscription_expires_at
            if current_expiry and current_expiry.tzinfo is None:
                current_expiry = current_expiry.replace(tzinfo=timezone.utc)

            bonus_days = 0
            info_msg = ""
            
            # Логіка перерахунку (Proration)
            if current_expiry and current_expiry > now:
                remaining_days = (current_expiry - now).days
                if remaining_days > 0 and user.subscription_tier in prices:
                    old_rate = prices[user.subscription_tier] / 30
                    new_rate = prices[tier] / 30
                    
                    # Заокруглення вгору на користь користувача
                    import math
                    bonus_days = math.ceil((remaining_days * old_rate) / new_rate)
                    
                    info_msg = (
                        f"📊 <b>Чесний перерахунок:</b>\n"
                        f"Ваш залишок ({remaining_days} дн. {user.subscription_tier.capitalize()}) "
                        f"конвертовано у <b>{bonus_days} бонусних днів</b> плану {tier.capitalize()}.\n\n"
                    )

            # Розрахунок нової дати: 30 днів + бонуси
            total_days = 30 + bonus_days
            new_expires_at = now + timedelta(days=total_days)
            
            stmt = update(User).where(User.id == user_id).values(
                subscription_tier=tier,
                subscription_expires_at=new_expires_at,
                bonus_days=bonus_days
            )
            await session.execute(stmt)
            await session.commit()
            
            logger.info(f"✅ User {user_id} upgraded to {tier} until {new_expires_at} (Bonus: {bonus_days})")
            
            await message.answer(
                f"🎉 <b>Дякуємо за підписку!</b>\n\n"
                f"{info_msg}"
                f"Ваш план: <b>{tier.capitalize()}</b>\n"
                f"Діє до: <b>{new_expires_at.strftime('%d.%m.%Y')}</b>\n"
                f"<i>(+{bonus_days} бонусних днів враховано)</i>\n\n"
                f"Слоти та функції Pulse вже активовані! ✨",
                parse_mode="HTML"
            )
