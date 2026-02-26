from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import Story, Publication, Channel
from services.digest import get_user_digest_data
from pydantic import BaseModel
from typing import List, Optional

from api.routes import catalog, billing, affiliate

import logging
import time
from fastapi import Request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Pulse Mini App API", version="1.0.0")

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(f"🚀 {request.method} {request.url.path} - {response.status_code} ({duration:.2f}s)")
    return response

# CORS config allowing Telegram WebApp access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, verify Telegram WebApp initData
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(catalog.router)
app.include_router(billing.router)
app.include_router(affiliate.router)

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# --- Pydantic Models ---
class Source(BaseModel):
    name: str
    url: Optional[str] = None

class StoryCompact(BaseModel):
    uid: str
    id: int
    type: str
    title: str
    summary: str
    category: str
    score: float
    sources: List[Source]
    url: Optional[str] = None
    publications_count: int

class BriefNews(BaseModel):
    uid: str
    id: int
    type: str
    title: str
    summary: str
    channel: str
    category: str
    sources: List[Source]
    url: Optional[str] = None
    time: str

class DigestResponse(BaseModel):
    # Category mode fields
    categories: Optional[dict] = None
    
    # Channel mode fields
    channels: Optional[dict] = None
    
    # Time mode fields
    items: Optional[List[dict]] = None
    
    has_more: bool = False
    stats: dict

class PublicationDetail(BaseModel):
    id: int
    channel_title: str
    content: Optional[str]
    url: Optional[str]
    published_at: str
    views: int

class StoryDetail(BaseModel):
    id: int
    title: Optional[str]
    summary: Optional[str]
    category: Optional[str]
    timeline: List[PublicationDetail]

# --- Endpoints ---

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/v1/digest/{user_id}", response_model=DigestResponse)
async def get_digest(
    user_id: int, 
    group_by: str = "category", 
    pinned: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """
    Get user digest (Top Stories + Briefs) with sorting options
    """
    try:
        pinned_list = pinned.split(",") if pinned else []
        data = await get_user_digest_data(
            user_id, 
            hours=120, 
            group_by=group_by, 
            pinned_categories=pinned_list,
            limit=limit,
            offset=offset
        )
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/story/{story_id}", response_model=StoryDetail)
async def get_story_detail(story_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get full details of a specific story with all linked publications (Timeline)
    """
    # 1. Get Story
    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()
    
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # 2. Get Publications
    stmt_pubs = (
        select(Publication)
        .join(Channel)
        .where(Publication.story_id == story_id)
        .order_by(Publication.published_at.desc())
    )
    res_pubs = await db.execute(stmt_pubs)
    publications = res_pubs.scalars().all()
    
    timeline = []
    for pub in publications:
        timeline.append({
            "id": pub.id,
            "channel_title": pub.channel.title if pub.channel else "Unknown",
            "content": pub.content,
            "url": pub.url,
            "published_at": pub.published_at.isoformat(),
            "views": pub.views
        })

    return {
        "id": story.id,
        "title": story.title,
        "summary": story.summary,
        "category": story.category,
        "timeline": timeline
    }
