from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import Channel, Auction, User
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])

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
        
    await db.commit()
    return {"status": "ok", "message": "Ставку прийнято"}
