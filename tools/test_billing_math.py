import datetime
from datetime import timedelta, timezone

# --- КОНСТАНТИ З НАШОГО КОДУ ---
TIER_PRICES = {
    "basic": 60,
    "standard": 90,
    "premium": 120
}

def calculate_new_subscription(current_tier, current_expires_at, new_tier, now):
    """
    Відтворення логіки з bot/handlers/billing.py
    """
    if new_tier == current_tier:
        # Логіка подовження
        base_time = max(current_expires_at, now)
        new_expires_at = base_time + timedelta(days=30)
        bonus_days = 0
    else:
        # Логіка апгрейду
        bonus_days = 0
        if current_tier in TIER_PRICES and current_expires_at > now:
            remaining_time = current_expires_at - now
            remaining_days = remaining_time.days + (remaining_time.seconds / 86400)
            
            current_daily_price = TIER_PRICES[current_tier] / 30
            new_daily_price = TIER_PRICES[new_tier] / 30
            bonus_days = (remaining_days * current_daily_price) / new_daily_price
        
        new_expires_at = now + timedelta(days=30 + bonus_days)
    
    return new_expires_at, bonus_days

def run_test(name, current_tier, expires_at_days, new_tier, now_offset_days=0):
    now = datetime.datetime.now(timezone.utc)
    current_expires_at = now + timedelta(days=expires_at_days)
    now_actual = now + timedelta(days=now_offset_days)
    
    new_expires, bonus = calculate_new_subscription(current_tier, current_expires_at, new_tier, now_actual)
    
    total_days = (new_expires - now_actual).days + (new_expires - now_actual).seconds / 86400
    
    print(f"--- TEST: {name} ---")
    print(f"Поточний план: {current_tier} (залишилось днів: {expires_at_days - now_offset_days})")
    print(f"Купуємо план: {new_tier}")
    print(f"Нараховано бонусних днів: {bonus:.2f}")
    print(f"Новий термін дії: {total_days:.2f} днів")
    print(f"Вартість дня для користувача: {(TIER_PRICES[new_tier] / 30):.2f} ⭐")
    
    # Перевірка "грошового еквіваленту"
    total_spent = TIER_PRICES[new_tier] + (expires_at_days - now_offset_days) * (TIER_PRICES[current_tier]/30)
    calculated_value = total_days * (TIER_PRICES[new_tier]/30)
    
    print(f"Загальна цінність (Stars): {calculated_value:.2f}")
    print(f"Чи збігається з витратами? {'✅ ТАК' if abs(total_spent - calculated_value) < 0.1 else '❌ НІ'}")
    print("\n")

if __name__ == "__main__":
    # Сценарій 1: Апгрейд у той же день
    run_test("Апгрейд у той же день (Basic -> Standard)", "basic", 30, "standard")
    
    # Сценарій 2: Апгрейд через 15 днів
    run_test("Апгрейд посеред терміну (Basic -> Premium через 15 днів)", "basic", 30, "premium", now_offset_days=15)
    
    # Сценарій 3: Каскад (Standard -> Premium через 1 хв після апгрейду)
    # Спочатку отримаємо стан після першого апгрейду
    print("=== КАСКАДНИЙ ТЕСТ (Basic -> Standard -> Premium) ===")
    now = datetime.datetime.now(timezone.utc)
    # Крок 1: Юзер на Basic, купує Standard
    exp1, bonus1 = calculate_new_subscription("basic", now + timedelta(days=30), "standard", now)
    # Крок 2: Юзер ВЖЕ на Standard (з новою датою), купує Premium
    exp2, bonus2 = calculate_new_subscription("standard", exp1, "premium", now)
    
    total_days = (exp2 - now).days + (exp2 - now).seconds / 86400
    print(f"Сумарно бонусних днів: {(bonus1 + bonus2):.2f}")
    print(f"Фінальний термін Premium: {total_days:.2f} днів")
    total_spent = 60 + 90 + 120 # Купив всі три плани
    calculated_value = total_days * (120/30) # Вартість Premium
    print(f"Загальна цінність: {calculated_value:.2f} ⭐ (Витрачено: {total_spent} ⭐)")
    print(f"Перевірка: {'✅ ТАК' if abs(total_spent - calculated_value) < 0.1 else '❌ НІ'}\n")

    # Сценарій 4: Подовження того ж плану
    run_test("Подовження того ж плану (Premium -> Premium)", "premium", 10, "premium")
