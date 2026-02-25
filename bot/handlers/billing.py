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
async def process_successful_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload
    parts = payload.split("_")
    
    # Payload format: sub_{tier}_{user_id}
    # Payload format: ad_{days}_{channel_id}_{user_id}
    # Payload format: bid_{category}_{channel_id}_{price}_{user_id}

    async with AsyncSessionLocal() as session:
        if parts[0] == "sub":
            tier = parts[1]
            user_id = int(parts[2])
            
            # Отримуємо поточного юзера для перевірки залишкового терміну
            # Ціни для розрахунку бонусів (мають співпадати з API)
            TIER_PRICES = {"basic": 60, "standard": 90, "premium": 120}
            
            from database.models import User
            from sqlalchemy import select
            user_res = await session.execute(select(User).where(User.id == user_id))
            user = user_res.scalar_one_or_none()
            
            now = datetime.now(timezone.utc)
            old_tier = user.subscription_tier if user else "demo"
            
            # Логіка визначення нового терміну
            if tier == old_tier:
                # 1. Подовження або Автоподовження того ж плану
                current_expires = user.subscription_expires_at.replace(tzinfo=timezone.utc) if user.subscription_expires_at else now
                base_time = max(current_expires, now)
                new_expires_at = base_time + timedelta(days=30)
                msg_text = f"✅ План **{tier.capitalize()}** продовжено на 30 днів! Дякуємо за довіру."
            else:
                # 2. Upgrade (перехід на вищий план)
                # Оскільки за Recurring-апгрейд ми беремо ПОВНУ ціну, компенсуємо залишок бонусними днями
                bonus_days = 0
                if user and old_tier in TIER_PRICES and user.subscription_expires_at:
                    current_expires = user.subscription_expires_at.replace(tzinfo=timezone.utc)
                    if current_expires > now:
                        remaining_time = current_expires - now
                        remaining_days = remaining_time.days + (remaining_time.seconds / 86400)
                        
                        current_daily_price = TIER_PRICES[old_tier] / 30
                        new_daily_price = TIER_PRICES[tier] / 30
                        bonus_days = (remaining_days * current_daily_price) / new_daily_price
                
                new_expires_at = now + timedelta(days=30 + bonus_days)
                bonus_str = f" (+{int(bonus_days)} бонусних днів)" if bonus_days >= 1 else ""
                msg_text = f"✅ План оновлено до **{tier.capitalize()}**!{bonus_str} Бажаємо приємного користування."

            # Нарахування бонусу рефереру
            # 1. Перевіряємо офіційну партнерку Telegram (Stars Affiliate)
            is_official_affiliate = False
            official_affiliate_user_id = None
            try:
                official_affiliate = getattr(message.successful_payment, "affiliate", None)
                if not official_affiliate and hasattr(message.successful_payment, "model_extra"):
                    official_affiliate = message.successful_payment.model_extra.get("affiliate")
                
                if official_affiliate:
                    is_official_affiliate = True
                    # Спробуємо витягнути ID афіліата (якщо це користувач, а не канал)
                    # AffiliateInfo.affiliate_user -> User.id
                    aff_user = getattr(official_affiliate, "affiliate_user", None)
                    if not aff_user and isinstance(official_affiliate, dict):
                        aff_user = official_affiliate.get("affiliate_user")
                    
                    if aff_user:
                        official_affiliate_user_id = getattr(aff_user, "id", None) or aff_user.get("id")
                    
                    logger.info(f"Official Telegram affiliate detected for user {user_id}. Payout handled by Telegram. Partner: {official_affiliate_user_id}")
            except Exception as e:
                logger.warning(f"Error checking official affiliate: {e}")

            # Якщо це офіційний афіліат, а у нас ще немає referrer_id, записуємо його!
            if is_official_affiliate and not user.referrer_id and official_affiliate_user_id:
                # Перевіряємо, чи такий реферер є в нашій базі
                ref_exists = await session.execute(select(User).where(User.id == official_affiliate_user_id))
                if ref_exists.scalar_one_or_none():
                    user.referrer_id = official_affiliate_user_id
                    logger.info(f"Linking user {user_id} to official affiliate {official_affiliate_user_id} in our DB.")

            if user.referrer_id:
                # Вираховуємо 10% комісії (згідно зі скріншотом)
                commission_pc = 0.10
                earned = TIER_PRICES[tier] * commission_pc
                
                # Оновлюємо кількість рефералів для реферера (якщо це його перша покупка)
                # Користувач вважається рефералом, якщо він вперше купив підписку
                is_first_real_referral = (old_tier == "demo")
                
                update_values = {}
                if is_first_real_referral:
                    update_values["referrals_count"] = User.referrals_count + 1
                
                # Тільки якщо це НЕ офіційна партнерка Telegram, нараховуємо Stars вручну
                if not is_official_affiliate:
                    update_values["affiliate_earned_stars"] = User.affiliate_earned_stars + earned
                    logger.info(f"Custom affiliate bonus {earned} stars credited to {user.referrer_id}")
                else:
                    logger.info(f"Skipping manual stars credit for {user.referrer_id} (handled by Telegram)")

                if update_values:
                    await session.execute(
                        update(User)
                        .where(User.id == user.referrer_id)
                        .values(**update_values)
                    )
            
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(subscription_tier=tier, subscription_expires_at=new_expires_at)
            )
            await message.answer(msg_text)
            
        elif parts[0] == "ad":
            days = int(parts[1])
            channel_id = int(parts[2])
            from database.models import Channel
            expires_at = datetime.now(timezone.utc) + timedelta(days=days)
            await session.execute(
                update(Channel)
                .where(Channel.id == channel_id)
                .values(partner_status="premium", partner_expires_at=expires_at)
            )
            await message.answer(f"✅ Канал активовано у Преміум-каруселі на {days} днів!")
            
        elif parts[0] == "bid":
            category = parts[1]
            channel_id = int(parts[2])
            amount = int(parts[3])
            user_id = int(parts[4])
            from database.models import Auction
            
            stmt = select(Auction).where(Auction.category == category)
            res = await session.execute(stmt)
            auction = res.scalar_one_or_none()
            
            if auction:
                auction.current_bid = amount
                auction.leader_user_id = user_id
                auction.channel_id = channel_id
            else:
                new_auc = Auction(
                    category=category,
                    current_bid=amount,
                    leader_user_id=user_id,
                    channel_id=channel_id,
                    ends_at=datetime.now(timezone.utc) + timedelta(hours=24)
                )
                session.add(new_auc)
            await message.answer(f"✅ Вашу ставку {amount} Stars у категорії '{category}' прийнято!")

        await session.commit()
