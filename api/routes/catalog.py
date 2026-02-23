from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import Channel, Auction, User, UserSubscription
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime, timedelta
import httpx
from fastapi.responses import StreamingResponse
from config.settings import config
import io

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])

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
    partner_status: str = "organic"
    posts_count_24h: int = 0
    can_unsubscribe_at: Optional[str] = None
    is_placeholder: bool = False # Для відображення порожніх слотів
    position: Optional[int] = 0

class AuctionBidRequest(BaseModel):
    user_id: int
    channel_id: int
    category: str
    amount: int  # Stars

# --- Endpoints ---

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Отримати список всіх унікальних категорій з кількістю каналів"""
    stmt = (
        select(Channel.category, func.count(Channel.id))
        .where(Channel.is_active == True)
        .group_by(Channel.category)
        .order_by(desc(func.count(Channel.id)))
    )
    result = await db.execute(stmt)
    categories = []
    for cat, count in result:
        if cat:
            categories.append({"name": cat, "channels_count": count})
    return categories

@router.get("/channels", response_model=List[ChannelCatalogItem])
async def get_channels(
    category: Optional[str] = None, 
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Отримати канали для каталогу з сортуванням:
    1. Premium (партнери)
    2. Pinned (закріплені)
    3. Organic (за активністю 24г)
    """
    stmt = select(Channel).where(Channel.is_active == True)
    
    if category:
        stmt = stmt.where(Channel.category == category)
        
    # Сортування: Партнерський статус (якщо є), потім кількість постів
    stmt = stmt.order_by(
        desc(Channel.partner_status == 'premium'),
        desc(Channel.partner_status == 'pinned'),
        desc(Channel.posts_count_24h)
    )
    
    result = await db.execute(stmt)
    channels_db = result.scalars().all()
    
    # Отримуємо підписки користувача, якщо user_id передано
    user_subs = set()
    if user_id:
        sub_stmt = select(UserSubscription.channel_id).where(UserSubscription.user_id == user_id)
        sub_res = await db.execute(sub_stmt)
        user_subs = set(sub_res.scalars().all())

    channels = []
    for ch in channels_db:
        # Fallback для аватарок
        avatar = ch.avatar_url or f"/api/v1/catalog/photo/{ch.telegram_id}"
        
        channels.append(ChannelCatalogItem(
            id=ch.id,
            username=ch.username,
            title=ch.title,
            category=ch.category,
            partner_status=ch.partner_status,
            posts_count_24h=ch.posts_count_24h,
            is_core=ch.is_core,
            avatar_url=avatar,
            is_subscribed=ch.id in user_subs
        ))
    return channels

@router.get("/my-channels/{user_id}", response_model=List[ChannelCatalogItem])
async def get_my_channels(user_id: int, db: AsyncSession = Depends(get_db)):
    """Отримати канали, на які підписаний користувач"""
    # Отримуємо ліміт користувача
    status = await get_user_status(user_id, db)
    user_limit = status["limit"]

    # Канали відсортовані за алфавітом у запиті, але для лімітів 
    # бекенд дайджесту використовує дату підписки. 
    # Тут ми зробимо так само для консистентності.
    from database.models import UserSubscription
    stmt = (
        select(Channel, UserSubscription.last_changed_at)
        .join(UserSubscription, Channel.id == UserSubscription.channel_id)
        .where(UserSubscription.user_id == user_id, Channel.is_active == True)
        .order_by(UserSubscription.position.asc(), UserSubscription.created_at.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    from datetime import timezone
    now = datetime.now(timezone.utc)
    
    channels = []
    for idx, (ch, last_changed) in enumerate(rows):
        avatar = ch.avatar_url or f"/api/v1/catalog/photo/{ch.telegram_id}"
        is_active_for_limit = idx < user_limit
        
        # Вираховуємо час розморозки
        can_unsubscribe_at = None
        if last_changed:
            # Завжди працюємо з UTC
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

class SubscribeRequest(BaseModel):
    user_id: int
    channel_id: int

class ReorderRequest(BaseModel):
    user_id: int
    channel_ids: List[int] # Список ID каналів у новому порядку

@router.post("/subscribe")
async def subscribe(req: SubscribeRequest, db: AsyncSession = Depends(get_db)):
    """Підписати користувача на канал"""
    # 1. Перевірити чи існує канал
    channel = await db.get(Channel, req.channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Канал не знайдено")
    
    # 2. Перевірити ліміти
    status = await get_user_status(req.user_id, db)
    if not status["can_add"]:
        raise HTTPException(status_code=403, detail=f"Ліміт вичерпано ({status['limit']} каналів)")

    # 3. Перевірити чи вже підписаний
    stmt = select(UserSubscription).where(
        UserSubscription.user_id == req.user_id,
        UserSubscription.channel_id == req.channel_id
    )
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        return {"status": "ok", "message": "Вже підписані"}
    
    # 4. Визначити наступну позицію для користувача
    pos_stmt = select(func.max(UserSubscription.position)).where(UserSubscription.user_id == req.user_id)
    pos_res = await db.execute(pos_stmt)
    max_pos = pos_res.scalar()
    next_pos = (max_pos + 1) if max_pos is not None else 0

    # 5. Додати підписку
    new_sub = UserSubscription(user_id=req.user_id, channel_id=req.channel_id, position=next_pos)
    db.add(new_sub)
    await db.commit()
    return {"status": "ok", "message": "Успішно підписано"}

@router.post("/reorder")
async def reorder_channels(req: ReorderRequest, db: AsyncSession = Depends(get_db)):
    """
    Змінити порядок слотів користувача (Drag-and-Drop).
    Обмеження: не частіше ніж раз на 24г.
    """
    from database.models import UserSubscription
    from datetime import timezone
    
    # 1. Перевірка cooldown
    stmt = select(UserSubscription).where(UserSubscription.user_id == req.user_id)
    res = await db.execute(stmt)
    all_subs = res.scalars().all()
    
    if not all_subs:
        return {"status": "ok"}
    
    # Перевіряємо самий свіжий last_changed_at серед всіх підписок
    last_change = max(s.last_changed_at for s in all_subs)
    lc_utc = last_change.replace(tzinfo=timezone.utc) if not last_change.tzinfo else last_change
    now = datetime.now(timezone.utc)
    cooldown_end = lc_utc + timedelta(hours=24)
    
    if now < cooldown_end:
        remaining = cooldown_end - now
        hours, remainder = divmod(int(remaining.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        time_str = f"{hours}г {minutes}хв" if hours > 0 else f"{minutes}хв"
        raise HTTPException(
            status_code=403, 
            detail=f"Змінювати порядок слотів можна раз на 24г. Залишилось: {time_str}"
        )
    
    # 2. Оновлення позицій
    id_to_sub = {s.channel_id: s for s in all_subs}
    for idx, ch_id in enumerate(req.channel_ids):
        if ch_id in id_to_sub:
            sub = id_to_sub[ch_id]
            sub.position = idx
            sub.last_changed_at = now
            
    await db.commit()
    return {"status": "ok"}

@router.post("/unsubscribe")
async def unsubscribe(req: SubscribeRequest, db: AsyncSession = Depends(get_db)):
    """Відписати користувача від каналу"""
    stmt = select(UserSubscription).where(
        UserSubscription.user_id == req.user_id,
        UserSubscription.channel_id == req.channel_id
    )
    res = await db.execute(stmt)
    sub = res.scalar_one_or_none()
    
    if sub:
        # Перевірка 24-годинного ліміту
        from datetime import timezone
        now = datetime.now(timezone.utc)
        lc_utc = sub.last_changed_at.replace(tzinfo=timezone.utc) if not sub.last_changed_at.tzinfo else sub.last_changed_at
        cooldown_end = lc_utc + timedelta(hours=24)
        
        if now < cooldown_end:
            remaining = cooldown_end - now
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            time_str = f"{hours}г {minutes}хв" if hours > 0 else f"{minutes}хв"
            
            raise HTTPException(
                status_code=403, 
                detail=f"Цей слот заморожено на 24г. Залишилось: {time_str}. Це захист від зловживань."
            )

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
        
@router.get("/user/status/{user_id}")
async def get_user_status(user_id: int, db: AsyncSession = Depends(get_db)):
    """Отримати статус підписки та кількість каналів"""
    user_res = await db.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()
    
    if not user:
        # Створити юзера якщо немає (базовий кейс)
        user = User(id=user_id, subscription_tier="demo")
        db.add(user)
        await db.commit()
    
    sub_count_res = await db.execute(
        select(func.count(UserSubscription.id)).where(UserSubscription.user_id == user_id)
    )
    sub_count = sub_count_res.scalar() or 0
    
    # Визначаємо ліміти
    limits = {
        "demo": 3,
        "basic": 10,
        "standard": 25,
        "premium": 999
    }
    
    user_tier = user.subscription_tier
    expires_at = None
    if user.subscription_expires_at:
        expires_at = user.subscription_expires_at.isoformat()
        # Якщо підписка закінчилась — скидаємо на demo (візуально)
        if user.subscription_expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
             user_tier = "demo"
    
    return {
        "tier": user_tier,
        "sub_count": sub_count,
        "limit": limits.get(user_tier, 3),
        "can_add": sub_count < limits.get(user_tier, 3),
        "expires_at": expires_at
    }

@router.post("/add-custom-channel")
async def add_custom_channel(req: CustomChannelRequest, db: AsyncSession = Depends(get_db)):
    """Додати власний канал за посиланням"""
    # 1. Перевірка лімітів
    status = await get_user_status(req.user_id, db)
    if not status["can_add"]:
        raise HTTPException(status_code=403, detail=f"Ви досягли ліміту ({status['limit']} каналів) для вашого плану")

    # 2. Парсинг username
    username = req.url.replace("https://t.me/", "").replace("@", "").split("/")[0]
    
    # 3. Валідація через Telegram Bot API
    token = config.BOT_TOKEN.get_secret_value()
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://api.telegram.org/bot{token}/getChat?chat_id=@{username}")
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Канал не знайдено або він приватний")
        
        chat_data = resp.json().get("result", {})
    
    # 4. Перевірка чи є канал в базі
    stmt = select(Channel).where(Channel.telegram_id == chat_data["id"])
    res = await db.execute(stmt)
    channel = res.scalar_one_or_none()
    
    if not channel:
        channel = Channel(
            telegram_id=chat_data["id"],
            username=chat_data.get("username"),
            title=chat_data.get("title", "Unknown"),
            category="Custom",
            is_core=False
        )
        db.add(channel)
        await db.flush()
    
    # 5. Підписка
    sub_stmt = select(UserSubscription).where(
        UserSubscription.user_id == req.user_id,
        UserSubscription.channel_id == channel.id
    )
    sub_res = await db.execute(sub_stmt)
    if sub_res.scalar_one_or_none():
        return {"status": "ok", "message": "Ви вже підписані на цей канал"}
    
    # 6. Fetch Avatar if needed
    try:
        if not channel.avatar_url:
            channel.avatar_url = f"/api/v1/catalog/photo/{channel.telegram_id}"
    except Exception:
        pass

    # 7. Визначити наступну позицію
    pos_stmt = select(func.max(UserSubscription.position)).where(UserSubscription.user_id == req.user_id)
    pos_res = await db.execute(pos_stmt)
    max_pos = pos_res.scalar()
    next_pos = (max_pos + 1) if max_pos is not None else 0

    new_sub = UserSubscription(user_id=req.user_id, channel_id=channel.id, position=next_pos)
    db.add(new_sub)
    await db.commit()
    
    return {"status": "ok", "message": "Канал успішно додано до ваших підписок"}

# Simple in-memory cache for file paths to reduce Telegram API calls
# telegram_id -> {"path": str, "expiry": datetime}
photo_path_cache = {}

@router.get("/photo/{telegram_id}")
async def get_channel_photo(telegram_id: int):
    """Проксі для отримання фото каналу через Telegram Bot API з кешуванням"""
    # 1. Перевірка кешу
    now = datetime.now()
    if telegram_id in photo_path_cache:
        cached = photo_path_cache[telegram_id]
        if now < cached["expiry"]:
            file_path = cached["path"]
            token = config.BOT_TOKEN.get_secret_value()
            photo_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
            
            async def stream_file():
                async with httpx.AsyncClient() as s_client:
                    async with s_client.stream("GET", photo_url) as r:
                        if r.status_code == 200:
                            async for chunk in r.aiter_bytes():
                                yield chunk
                        else:
                            # Якщо шлях застарів (наприклад, Telegram видалив файл), зачищаємо кеш
                            photo_path_cache.pop(telegram_id, None)

            return StreamingResponse(stream_file(), media_type="image/jpeg")

    token = config.BOT_TOKEN.get_secret_value()
    async with httpx.AsyncClient() as client:
        # 1. Get Chat to find big photo file_id
        # Normalize ID: Channels must start with -100
        chat_id = telegram_id
        if chat_id > 0:
            chat_id = int(f"-100{chat_id}")
            
        chat_resp = await client.get(f"https://api.telegram.org/bot{token}/getChat?chat_id={chat_id}")
        if chat_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Чат не знайдено")
        
        chat_info = chat_resp.json().get("result", {})
        photo = chat_info.get("photo")
        if not photo:
            raise HTTPException(status_code=404, detail="Фото відсутнє")
        
        file_id = photo.get("big_file_id") or photo.get("small_file_id")
        
        # 2. Get File Path
        file_resp = await client.get(f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}")
        if file_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Файл не знайдено")
        
        file_path = file_resp.json().get("result", {}).get("file_path")
        
        # 3. Update Cache (valid for 30 days)
        photo_path_cache[telegram_id] = {
            "path": file_path,
            "expiry": now + timedelta(days=30)
        }
        
        # 4. Stream from Telegram
        photo_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
        
        async def stream_file():
            async with httpx.AsyncClient() as s_client:
                async with s_client.stream("GET", photo_url) as r:
                    async for chunk in r.aiter_bytes():
                        yield chunk

        return StreamingResponse(stream_file(), media_type="image/jpeg")
