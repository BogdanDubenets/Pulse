from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import Channel, Auction, User, UserSubscription, Category, ChannelCategory
from services.subscription_service import subscription_service
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import httpx
from fastapi.responses import StreamingResponse, FileResponse
from config.settings import config
import io
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])

# Build verification: 6500037_v5_461874849

# --- Pydantic Models ---

class CustomChannelRequest(BaseModel):
    user_id: int
    url: str  # t.me/username or @username

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# --- Pydantic Models ---

class CategoryResponse(BaseModel):
    name: str
    channels_count: int

class ChannelCatalogItem(BaseModel):
    id: int
    username: Optional[str] = None
    title: str
    category: Optional[str] = None
    is_core: bool = False
    avatar_url: Optional[str] = None
    is_subscribed: bool = False
    is_limit_active: bool = True
    partner_status: Optional[str] = "organic"
    posts_count_24h: Optional[int] = 0
    can_unsubscribe_at: Optional[str] = None
    is_placeholder: bool = False # Для відображення порожніх слотів
    position: Optional[int] = 0
    subs_total: Optional[int] = 0

class AuctionBidRequest(BaseModel):
    user_id: int
    channel_id: int
    category: str
    amount: int  # Stars

class PremiumBuyRequest(BaseModel):
    user_id: int
    channel_id: int
    category: str
    days: int

class PartnerVerifyRequest(BaseModel):
    user_id: int
    channel_id: int

# --- Endpoints ---

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Отримати список всіх видимих категорій з БД з підрахунком активних каналів"""
    # Підраховуємо кількість каналів, які мають хоча б один пост у цій категорії
    subq = (
        select(ChannelCategory.category_id, func.count(ChannelCategory.channel_id).label("count"))
        .group_by(ChannelCategory.category_id)
        .subquery()
    )
    
    stmt = (
        select(Category, func.coalesce(subq.c.count, 0))
        .outerjoin(subq, Category.id == subq.c.category_id)
        .where(Category.is_visible == True)
        .order_by(desc(func.coalesce(subq.c.count, 0)), Category.name.asc())
    )
    
    result = await db.execute(stmt)
    categories = []
    for cat, count in result:
        categories.append({"name": f"{cat.emoji} {cat.name}", "channels_count": count})
    return categories

@router.get("/channels", response_model=List[ChannelCatalogItem])
async def get_channels(
    category: Optional[str] = None, 
    user_id: Optional[int] = None,
    sort: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Отримати канали для каталогу з сортуванням:
    1. Якщо sort=="popularity" - за кількістю підписок (Top-50)
    2. Інакше (за категорією): Auction -> Premium -> Pinned -> Organic
    """
    now = datetime.now(timezone.utc)
    
    if sort == "popularity":
        # Спеціальна логіка для топ-популярних каналів по всій системі
        # Підраховуємо кількість підписок для кожного активного каналу
        stmt = (
            select(
                Channel, 
                func.count(UserSubscription.id).label("subs_total")
            )
            .outerjoin(UserSubscription, Channel.id == UserSubscription.channel_id)
            .where(Channel.is_active == True)
            .group_by(Channel.id)
            .order_by(desc("subs_total"), Channel.posts_count_24h.desc())
            .limit(50)
        )
        result = await db.execute(stmt)
        channels_db = []
        for ch, count in result.all():
            ch.subs_total = count
            channels_db.append(ch)
        auction_channel_id = None # В глобальному топі аукціони категорій не показуємо або ігноруємо
    else:
        # Логіка для категорій: використовуємо ChannelCategory для визначення активності
        # Якщо категорія передана, ми фільтруємо канали, які в ній активні
        stmt = (
            select(
                Channel, 
                func.count(UserSubscription.id).label("subs_total"),
                func.coalesce(ChannelCategory.posts_count, 0).label("cat_activity")
            )
            .outerjoin(UserSubscription, Channel.id == UserSubscription.channel_id)
        )
        
        if category:
            # Парсимо назву категорії (прибираємо емодзі якщо є)
            clean_cat = category.split(" ", 1)[-1] if " " in category else category
            cat_stmt = select(Category.id).where(Category.name == clean_cat)
            cat_res = await db.execute(cat_stmt)
            cat_id = cat_res.scalar()
            
            if cat_id:
                # JOIN з ChannelCategory для фільтрації та отримання активності
                stmt = stmt.join(ChannelCategory, (Channel.id == ChannelCategory.channel_id) & (ChannelCategory.category_id == cat_id))
            else:
                # Fallback на стару логіку за рядком, якщо категорія не в новій таблиці
                stmt = stmt.where(Channel.category == category)
        else:
            # Якщо категорія не вказана, просто LEFT JOIN
            stmt = stmt.outerjoin(ChannelCategory, Channel.id == ChannelCategory.channel_id)

        stmt = (
            stmt.where(Channel.is_active == True)
            .group_by(Channel.id, ChannelCategory.posts_count if category else Channel.id) # group_by fix
        )
        
        # Виконуємо запит
        result = await db.execute(stmt)
        
        channels_db = []
        for row in result.all():
            ch = row[0]
            ch.subs_total = row[1]
            ch.cat_activity = row[2]
            channels_db.append(ch)
        
        # 2. Отримуємо переможця аукціону для категорії
        auction_channel_id = None
        if category:
            auction_stmt = select(Auction.channel_id).where(Auction.category == category, Auction.ends_at > now).order_by(desc(Auction.current_bid))
            auction_res = await db.execute(auction_stmt)
            auction_channel_id = auction_res.scalar()

    # 3. Розподіляємо канали по тірах (якщо не сортування за популярністю)
    combined_channels = []
    if sort == "popularity":
        combined_channels = channels_db
    else:
        auction_winners = []
        premium_channels = []
        pinned_channels = []
        organic_channels = []

        for ch in channels_db:
            # Перевірка терміну дії статусу
            status = ch.partner_status
            if ch.partner_expires_at and ch.partner_expires_at.replace(tzinfo=timezone.utc) < now:
                status = "organic"

            if ch.id == auction_channel_id:
                auction_winners.append(ch)
            elif status == "premium":
                premium_channels.append(ch)
            elif status == "pinned":
                pinned_channels.append(ch)
            else:
                organic_channels.append(ch)

        # 4. Сортування органіки: за активністю в КАТЕГОРІЇ, якщо вона є, інакше за 24г
        if category:
            organic_channels.sort(key=lambda x: getattr(x, "cat_activity", 0), reverse=True)
        else:
            organic_channels.sort(key=lambda x: x.posts_count_24h, reverse=True)
            
        combined_channels = auction_winners + premium_channels + pinned_channels + organic_channels
    
    # Отримуємо підписки користувача, якщо user_id передано
    user_subs = set()
    if user_id:
        sub_stmt = select(UserSubscription.channel_id).where(UserSubscription.user_id == user_id)
        sub_res = await db.execute(sub_stmt)
        user_subs = set(sub_res.scalars().all())

    channels = []
    for ch in combined_channels:
        # Пріоритетно використовуємо системний шлях через проксі
        username_query = f"?username={ch.username}" if ch.username else ""
        avatar = f"/api/v1/catalog/photo/{ch.telegram_id}{username_query}"
        
        # Визначаємо статус для фронтенда (з урахуванням протухання)
        effective_status = ch.partner_status
        if ch.partner_expires_at and ch.partner_expires_at.replace(tzinfo=timezone.utc) < now:
            effective_status = "organic"
        
        # Якщо це переможець аукціону — ставимо окремий статус auction
        if ch.id == auction_channel_id:
            effective_status = "auction"

        channels.append(ChannelCatalogItem(
            id=ch.id,
            username=ch.username,
            title=ch.title,
            category=ch.category,
            partner_status=effective_status,
            posts_count_24h=ch.posts_count_24h,
            is_core=ch.is_core,
            avatar_url=avatar,
            is_subscribed=ch.id in user_subs,
            subs_total=getattr(ch, "subs_total", 0)
        ))
    return channels

@router.get("/my-channels/{user_id}", response_model=List[ChannelCatalogItem])
async def get_my_channels(user_id: int, db: AsyncSession = Depends(get_db)):
    """Отримати канали, на які підписаний користувач"""
    # Отримуємо ліміт користувача
    status = await subscription_service.get_user_status(user_id, db)
    user_limit = status["limit"]

    try:
        # Канали відсортовані за позицією
        from database.models import UserSubscription
        stmt = (
            select(Channel, UserSubscription.last_changed_at)
            .join(UserSubscription, Channel.id == UserSubscription.channel_id)
            .where(UserSubscription.user_id == user_id, Channel.is_active == True)
            .order_by(func.coalesce(UserSubscription.position, 999).asc(), UserSubscription.created_at.asc())
        )
        result = await db.execute(stmt)
        rows = result.all()
        
        now = datetime.now(timezone.utc)
        
        channels = []
        for idx, (ch, last_changed) in enumerate(rows):
            # Пріоритетно використовуємо системний шлях через проксі
            username_query = f"?username={ch.username}" if ch.username else ""
            avatar = f"/api/v1/catalog/photo/{ch.telegram_id}{username_query}"
            is_active_for_limit = idx < user_limit
            
            # Вираховуємо час розморозки
            can_unsubscribe_at = None
            if last_changed:
                lc_utc = last_changed.replace(tzinfo=timezone.utc) if not last_changed.tzinfo else last_changed
                cooldown_end = lc_utc + timedelta(hours=24)
                can_unsubscribe_at = cooldown_end.isoformat()
            
            channels.append(ChannelCatalogItem(
                id=ch.id,
                username=ch.username,
                title=ch.title,
                category=ch.category,
                partner_status=ch.partner_status,
                posts_count_24h=ch.posts_count_24h,
                is_core=ch.is_core,
                avatar_url=avatar,
                is_subscribed=True,
                is_limit_active=is_active_for_limit,
                can_unsubscribe_at=can_unsubscribe_at,
                position=idx
            ))
        
        # Додаємо порожні слоти (placeholders) до повного ліміту
        current_count = len(channels)
        if current_count < user_limit:
            for i in range(current_count, user_limit):
                channels.append(ChannelCatalogItem(
                    id=-1 - i,
                    title=f"Слот #{i+1} (Порожній)",
                    is_placeholder=True,
                    is_limit_active=True,
                    position=i,
                    is_core=False
                ))

        return channels
    except Exception as e:
        logger.error(f"Error in get_my_channels for user {user_id}: {str(e)}", exc_info=True)
        # Повертаємо хоча б щось, щоб фронтенд не падав повністю, або прокидаємо HTTPException
        raise HTTPException(status_code=500, detail="Internal server error while loading your channels")

class SubscribeRequest(BaseModel):
    user_id: int
    channel_id: int

class ReorderRequest(BaseModel):
    user_id: int
    channel_ids: List[int] # Список ID каналів у новому порядку

@router.post("/subscribe")
async def subscribe(req: SubscribeRequest, db: AsyncSession = Depends(get_db)):
    """
    Підписати користувача на канал.
    Sales Trigger: якщо ліміту немає — запис НЕ створюється, повертаємо 403.
    """
    try:
        # 1. Перевірити чи існує канал
        channel = await db.get(Channel, req.channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Канал не знайдено")
        
        # 2. Отримуємо статус лімітів
        status = await subscription_service.get_user_status(req.user_id, db)
        
        # 3. Перевірити чи вже підписаний
        stmt = select(UserSubscription).where(
            UserSubscription.user_id == req.user_id,
            UserSubscription.channel_id == req.channel_id
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            return {"status": "ok", "message": "Вже підписані"}

        # 4. ЖОРСТКА ПЕРЕВІРКА ЛІМІТУ
        if not status["can_add"]:
            raise HTTPException(
                status_code=403, 
                detail=f"LIMIT_EXCEEDED|{status['limit']}" # Тригер для Mini App показати вікно оплати
            )

        # 6. Оновлення таймера (тільки при успішному додаванні) та додавання підписки
        user.last_config_change_at = datetime.now(timezone.utc)

        pos_stmt = select(func.max(UserSubscription.position)).where(UserSubscription.user_id == req.user_id)
        pos_res = await db.execute(pos_stmt)
        max_pos = pos_res.scalar()
        next_pos = (max_pos + 1) if max_pos is not None else 0

        new_sub = UserSubscription(user_id=req.user_id, channel_id=req.channel_id, position=next_pos)
        db.add(new_sub)
        await db.commit()

        return {"status": "ok", "message": "Успішно підписано"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in subscribe for user {req.user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during subscription")

@router.post("/reorder")
async def reorder_channels(req: ReorderRequest, db: AsyncSession = Depends(get_db)):
    """
    Змінити порядок слотів користувача (Drag-and-Drop).
    Глобальне обмеження: 1 зміна на 24г.
    """
    # 1. Перевірка Cooldown
    user = await db.get(User, req.user_id)
    if user and user.last_config_change_at:
        now = datetime.now(timezone.utc)
        lc_utc = user.last_config_change_at.replace(tzinfo=timezone.utc) if not user.last_config_change_at.tzinfo else user.last_config_change_at
        cooldown_end = lc_utc + timedelta(hours=24)
        if now < cooldown_end:
            remaining = cooldown_end - now
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            time_str = f"{hours}г {minutes}хв" if hours > 0 else f"{minutes}хв"
            raise HTTPException(
                status_code=403, 
                detail=f"Змінювати черговість можна раз на 24г. Залишилось: {time_str}"
            )

    # 2. Отримати всі підписки
    stmt = select(UserSubscription).where(UserSubscription.user_id == req.user_id)
    res = await db.execute(stmt)
    all_subs = res.scalars().all()
    
    if not all_subs:
        return {"status": "ok"}

    now = datetime.now(timezone.utc)
    id_to_sub = {s.channel_id: s for s in all_subs}
    for idx, ch_id in enumerate(req.channel_ids):
        if ch_id in id_to_sub:
            sub = id_to_sub[ch_id]
            sub.position = idx
            sub.last_changed_at = now
    
    # Оновлюємо глобальний таймер
    if user:
        user.last_config_change_at = now
            
    await db.commit()
    return {"status": "ok"}

@router.post("/unsubscribe")
async def unsubscribe(req: SubscribeRequest, db: AsyncSession = Depends(get_db)):
    """Відписати користувача від каналу (також активує 24г cooldown)"""
    stmt = select(UserSubscription).where(
        UserSubscription.user_id == req.user_id,
        UserSubscription.channel_id == req.channel_id
    )
    res = await db.execute(stmt)
    sub = res.scalar_one_or_none()
    
    if sub:
        # Перевірка Global Cooldown
        user = await db.get(User, req.user_id)
        if user and user.last_config_change_at:
            now = datetime.now(timezone.utc)
            lc_utc = user.last_config_change_at.replace(tzinfo=timezone.utc) if not user.last_config_change_at.tzinfo else user.last_config_change_at
            cooldown_end = lc_utc + timedelta(hours=24)
            if now < cooldown_end:
                remaining = cooldown_end - now
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                time_str = f"{hours}г {minutes}хв" if hours > 0 else f"{minutes}хв"
                raise HTTPException(
                    status_code=403, 
                    detail=f"Змінювати активну підписку можна раз на 24г. Залишилось: {time_str}"
                )
        
        if user:
            user.last_config_change_at = datetime.now(timezone.utc)

        await db.delete(sub)
        await db.commit()
    
    return {"status": "ok", "message": "Успішно відписано"}

@router.post("/auction/bid")
async def place_bid(bid: AuctionBidRequest, db: AsyncSession = Depends(get_db)):
    """Ставка в аукціоні за Top-1 місце в категорії"""
    # 1. Перевірити чи існує аукціон для цієї категорії
    stmt = select(Auction).where(Auction.category == bid.category)
    result = await db.execute(stmt)
    auction = result.scalar_one_or_none()
    
    if auction:
        if bid.amount <= auction.current_bid:
            raise HTTPException(status_code=400, detail="Тиха ставка має бути вищою за поточну")
        
        auction.current_bid = bid.amount
        auction.leader_user_id = bid.user_id
        auction.channel_id = bid.channel_id
        # Продовжити час аукціону якщо до кінця мало часу? (Опціонально)
    else:
        # Створити новий аукціон (наприклад на 24 години)
        new_auction = Auction(
            category=bid.category,
            current_bid=bid.amount,
            leader_user_id=bid.user_id,
            channel_id=bid.channel_id,
            ends_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.add(new_auction)
    
    await db.commit()
    return {"status": "ok"}

@router.get("/auctions")
async def get_all_auctions(db: AsyncSession = Depends(get_db)):
    """Отримати всі активні аукціони для Кабінету"""
    # Отримуємо всі унікальні видимі категорії з БД
    cat_stmt = select(Category).where(Category.is_visible == True)
    cat_res = await db.execute(cat_stmt)
    categories = [f"{cat.emoji} {cat.name}" for cat in cat_res.scalars().all()]

    # Отримуємо фактичні аукціони
    now = datetime.now(timezone.utc)
    auc_stmt = select(Auction).where(Auction.ends_at > now)
    auc_res = await db.execute(auc_stmt)
    active_auctions = {a.category: a for a in auc_res.scalars().all()}

    results = []
    for cat in categories:
        auc = active_auctions.get(cat)
        results.append({
            "category": cat,
            "current_bid": auc.current_bid if auc else 0,
            "leader_user_id": auc.leader_user_id if auc else None,
            "ends_at": auc.ends_at.isoformat() if auc else None,
            "has_active_auction": auc is not None
        })
    
    return results

@router.post("/premium/buy")
async def buy_premium_slot(req: PremiumBuyRequest, db: AsyncSession = Depends(get_db)):
    """Купівля місця в каруселі (Tier 2)"""
    channel = await db.get(Channel, req.channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Канал не знайдено")
    
    # В реальності тут була б перевірка оплати
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(days=req.days)
    
    channel.partner_status = "premium"
    channel.partner_expires_at = expiry
    
    await db.commit()
    return {"status": "ok", "message": f"Статус Premium активовано до {expiry.date()}"}

@router.post("/partner/verify")
async def verify_partner_pin(req: PartnerVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Перевірка закрепу (Tier 3)"""
    channel = await db.get(Channel, req.channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Канал не знайдено")
    
    # TODO: Реальна логіка перевірки закрепу через Telegram API
    # Наразі просто імітуємо успіх для тестів
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(days=7) # Закреп діє 7 днів до наступної перевірки
    
    channel.partner_status = "pinned"
    channel.partner_expires_at = expiry
    
    await db.commit()
    return {"status": "ok", "message": "Закреп підтверджено! Статус діє 7 днів."}
@router.get("/user/status/{user_id}")
async def get_user_status_endpoint(user_id: int, db: AsyncSession = Depends(get_db)):
    """Отримати статус підписки та кількість каналів"""
    return await subscription_service.get_user_status(user_id, db)

@router.post("/add-custom-channel")
async def add_custom_channel(req: CustomChannelRequest, db: AsyncSession = Depends(get_db)):
    """Додати власний канал за посиланням"""
    # 1. Перевірка плану (власні канали тільки для платних)
    status = await subscription_service.get_user_status(req.user_id, db)
    if status["tier"] == "demo":
         raise HTTPException(status_code=403, detail="Додавання власних каналів доступне лише на платних планах. Будь ласка, виберіть з каталогу або покращте план.")
    
    # 2. ЖОРСТКА ПЕРЕВІРКА ЛІМІТУ
    if not status["can_add"]:
        raise HTTPException(
            status_code=403, 
            detail=f"LIMIT_EXCEEDED|{status['limit']}"
        )

    # 3. Парсинг username
    username = req.url.replace("https://t.me/", "").replace("@", "").split("/")[0]
    
    # 4. Валідація через Telegram Bot API
    token = config.BOT_TOKEN.get_secret_value()
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://api.telegram.org/bot{token}/getChat?chat_id=@{username}")
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Канал не знайдено в Telegram")
        
        tg_data = resp.json().get("result", {})
        
        # 4. Перевірити чи існує канал в нашій базі
        stmt = select(Channel).where(Channel.telegram_id == tg_data["id"])
        res = await db.execute(stmt)
        channel = res.scalar_one_or_none()
        
        if not channel:
            channel = Channel(
                telegram_id=tg_data["id"],
                username=tg_data.get("username"),
                title=tg_data.get("title", "Unknown"),
                is_active=True
            )
            db.add(channel)
            await db.flush()

    # 5. Перевірити чи вже підписаний
    stmt = select(UserSubscription).where(
        UserSubscription.user_id == req.user_id,
        UserSubscription.channel_id == channel.id
    )
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        return {"status": "ok", "message": "Вже підписані"}

    # 7. Оновлення таймера та додавання підписки
    if not user:
        # Безпечна ініціалізація
        user = User(
            id=req.user_id,
            subscription_tier="demo",
            is_active=True
        )
        db.add(user)
        await db.flush()

    if user:
        user.last_config_change_at = datetime.now(timezone.utc)

    pos_stmt = select(func.max(UserSubscription.position)).where(UserSubscription.user_id == req.user_id)
    pos_res = await db.execute(pos_stmt)
    max_pos = pos_res.scalar()
    next_pos = (max_pos + 1) if max_pos is not None else 0

    # 8. Додати підписку
    new_sub = UserSubscription(user_id=req.user_id, channel_id=channel.id, position=next_pos)
    db.add(new_sub)
    await db.commit()

    return {"status": "ok", "message": "Успішно підписано"}

# Simple in-memory cache for file paths to reduce Telegram API calls
@router.get("/photo/{telegram_id}")
async def get_channel_photo(telegram_id: int, username: Optional[str] = None):
    """Отримати фото каналу: спочатку з диска, якщо немає - завантажити з Telegram"""
    from api.utils.storage import get_or_download_avatar
    from fastapi.responses import FileResponse
    
    try:
        file_path = await get_or_download_avatar(telegram_id, username=username)
        
        if file_path and os.path.exists(file_path):
            return FileResponse(file_path, media_type="image/jpeg")
            
        logger.warning(f"Avatar file not found for {telegram_id} at {file_path}")
        raise HTTPException(status_code=404, detail="Avatar not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve avatar for {telegram_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
