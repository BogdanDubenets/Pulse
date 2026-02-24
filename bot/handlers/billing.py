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
            from database.models import User
            from sqlalchemy import select
            user_res = await session.execute(select(User).where(User.id == user_id))
            user = user_res.scalar_one_or_none()
            
            now = datetime.now(timezone.utc)
            
            # Якщо це продовження того ж самого плану (Extension), додаємо 30 днів до поточного терміну
            if user and user.subscription_tier == tier and user.subscription_expires_at:
                current_expires = user.subscription_expires_at.replace(tzinfo=timezone.utc) if not user.subscription_expires_at.tzinfo else user.subscription_expires_at
                base_time = max(current_expires, now)
                new_expires_at = base_time + timedelta(days=30)
                msg_text = f"✅ План **{tier.capitalize()}** продовжено на 30 днів! Дякуємо за довіру."
            else:
                # Якщо це Upgrade (або нова підписка), встановлюємо 30 днів від сьогодні
                # Оскільки за Upgrade ми дали знижку в Stars за НЕВИКОРИСТАНІ дні
                new_expires_at = now + timedelta(days=30)
                msg_text = f"✅ План оновлено до **{tier.capitalize()}**! Бажаємо приємного користування."
            
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(subscription_tier=tier, subscription_expires_at=new_expires_at)
            )
            await message.answer(f"✅ План оновлено до **{tier.capitalize()}**! Бажаємо приємного користування.")
            
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
