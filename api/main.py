from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import AsyncSessionLocal
from database.models import Story, Publication, Channel
from services.digest import get_user_digest_data
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Pulse Mini App API", version="1.0.0")

# CORS config allowing Telegram WebApp access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, verify Telegram WebApp initData
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    pinned: Optional[str] = None
):
    """
    Get user digest (Top Stories + Briefs) with sorting options
    """
    try:
        pinned_list = pinned.split(",") if pinned else []
        data = await get_user_digest_data(
            user_id, 
            hours=24, 
            group_by=group_by, 
            pinned_categories=pinned_list
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
