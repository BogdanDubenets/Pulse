import asyncio
from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import User
from database.users import upsert_user
from api.routes.affiliate import get_affiliate_stats
from datetime import datetime, timezone

async def test_successful_payment_official(session: AsyncSession, user_id: int, referrer_id: int):
    """Тестування офіційного афіліата Telegram"""
    print("\n--- Тестування Офіційного Афіліата Telegram ---")
    
    # Скидаємо реферера у користувача для чистоти тесту
    await session.execute(text(f"UPDATE users SET referrer_id = NULL WHERE id = {user_id}"))
    await session.commit()
    
    # Імітуємо об'єкт SuccessfulPayment з полем affiliate
    class MockAffiliateUser:
        def __init__(self, id):
            self.id = id

    class MockAffiliate:
        def __init__(self, user_id):
            self.affiliate_user = MockAffiliateUser(user_id)

    class MockPayment:
        def __init__(self, aff_id):
            self.successful_payment = type('obj', (object,), {
                'total_amount': 500,
                'invoice_payload': 'tier_pro',
                'affiliate': MockAffiliate(aff_id)
            })
            self.from_user = type('obj', (object,), {'id': user_id})

    message = MockPayment(referrer_id)
    
    # Отримуємо реферера ДО тесту
    ref_before = await session.execute(select(User).where(User.id == referrer_id))
    ref_before = ref_before.scalar_one()
    stars_before = ref_before.affiliate_earned_stars
    count_before = ref_before.referrals_count

    # Викликаємо обробник
    from bot.handlers.billing import process_successful_payment
    await process_successful_payment(message, session)

    # Перевіряємо результат
    await session.refresh(ref_before)
    user_after = await session.get(User, user_id)
    
    print(f"Зірки після: {ref_before.affiliate_earned_stars} (очікуємо {stars_before}, бо це ОФІЦІЙНА виплата)")
    print(f"Кількість рефералів: {ref_before.referrals_count} (очікуємо {count_before + 1})")
    print(f"Referrer ID у покупця: {user_after.referrer_id} (очікуємо {referrer_id} - автоприв'язка)")

    assert ref_before.affiliate_earned_stars == stars_before
    assert ref_before.referrals_count == count_before + 1
    assert user_after.referrer_id == referrer_id
    print("✅ Тест офіційного афіліата пройдено!")

async def test_affiliate_flow():
    user_id = 999999
    referrer_id = 888888
    
    print(f"--- Testing Affiliate Flow ---")
    
    async with AsyncSessionLocal() as session:
        # 1. Clean up old test data
        await session.execute(text("DELETE FROM users WHERE id IN (999999, 888888)"))
        await session.commit()
        
        # 2. Create referrer
        print(f"Step 0: Creating referrer {referrer_id}")
        await upsert_user(referrer_id, "Referrer User", "ref_user")
        
        # 3. Register user with referrer
        print(f"Step 1: Upserting user {user_id} with referrer {referrer_id}")
        await upsert_user(user_id, "Test User", "test_user", referrer_id=referrer_id)
        
        # 3. Verify referrer_id saved
        res = await session.execute(select(User).where(User.id == user_id))
        user = res.scalar_one()
        print(f"User referrer_id: {user.referrer_id} (Expected: {referrer_id})")
        assert user.referrer_id == referrer_id
        
        # 4. Simulate payment (Logic from bot/handlers/billing.py)
        # Assuming Pulse Pro (100 stars) -> 20% = 20 stars commission
        tier_price = 100
        commission = tier_price * 0.20
        print(f"Step 2: Simulating payment of {tier_price} stars. Crediting {commission} to referrer.")
        
        await session.execute(
            update(User)
            .where(User.id == referrer_id)
            .values(
                affiliate_earned_stars=User.affiliate_earned_stars + commission,
                referrals_count=User.referrals_count + 1
            )
        )
        await session.commit()
        
        # 5. Check stats via API logic
        print(f"Step 3: Checking stats via API logic")
        from fastapi import HTTPException
        try:
            stats = await get_affiliate_stats(referrer_id, session)
            print(f"Stats: Link={stats.referral_link}, Earned={stats.earned_stars}, Refs={stats.referrals_count}")
            assert stats.earned_stars == commission
            assert stats.referrals_count == 1
        except Exception as e:
            print(f"API Error: {e}")
            raise e

    print(f"✅ Affiliate test PASSED")

if __name__ == "__main__":
    asyncio.run(test_affiliate_flow())
