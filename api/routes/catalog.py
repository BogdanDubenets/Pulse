from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import Channel, Auction, User, UserSubscription
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime
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
    username: Optional[str]
    title: str
    category: Optional[str]
    partner_status: str
    posts_count_24h: int
    is_core: bool
    avatar_url: Optional[str] = None

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
    # В майбутньому тут буде складніша логіка з урахуванням Аукціону Top-1
    stmt = stmt.order_by(
        desc(Channel.partner_status == 'premium'),
        desc(Channel.partner_status == 'pinned'),
        desc(Channel.posts_count_24h)
    )
    
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/my-channels/{user_id}", response_model=List[ChannelCatalogItem])
async def get_my_channels(user_id: int, db: AsyncSession = Depends(get_db)):
    """Отримати канали, на які підписаний користувач"""
    from database.models import UserSubscription
    stmt = (
        select(Channel)
        .join(UserSubscription, Channel.id == UserSubscription.channel_id)
        .where(UserSubscription.user_id == user_id, Channel.is_active == True)
        .order_by(Channel.title)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

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
        from datetime import timedelta
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
    
    return {
        "tier": user.subscription_tier,
        "sub_count": sub_count,
        "limit": limits.get(user.subscription_tier, 3),
        "can_add": sub_count < limits.get(user.subscription_tier, 3)
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

    new_sub = UserSubscription(user_id=req.user_id, channel_id=channel.id)
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
        chat_resp = await client.get(f"https://api.telegram.org/bot{token}/getChat?chat_id={telegram_id}")
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
