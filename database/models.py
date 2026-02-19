from datetime import datetime
from typing import List, Optional
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

class Base(DeclarativeBase):
    pass

class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String)
    credibility_score: Mapped[float] = mapped_column(Float, default=0.5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_scanned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    publications: Mapped[List["Publication"]] = relationship(back_populates="channel")

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True) # Telegram User ID
    first_name: Mapped[Optional[str]] = mapped_column(String)
    username: Mapped[Optional[str]] = mapped_column(String)
    language_code: Mapped[Optional[str]] = mapped_column(String, default="uk")
    
    # Digest Settings
    morning_digest_time: Mapped[Optional[str]] = mapped_column(String, default="08:00") # "HH:MM"
    evening_digest_time: Mapped[Optional[str]] = mapped_column(String, default="20:00") # "HH:MM"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

class Story(Base):
    __tablename__ = "stories"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(Text)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String, default="pending")
    # Gemini embedding-001 returns 768 dimensions.
    embedding_vector: Mapped[Optional[Vector]] = mapped_column(Vector(768))

    publications: Mapped[List["Publication"]] = relationship(back_populates="story")

class Publication(Base):
    __tablename__ = "publications"

    id: Mapped[int] = mapped_column(primary_key=True)
    story_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"))
    channel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"))
    telegram_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String)
    url: Mapped[Optional[str]] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0)
    reactions: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    story: Mapped["Story"] = relationship(back_populates="publications")
    channel: Mapped["Channel"] = relationship(back_populates="publications")

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False) # Telegram User ID. Can be ForeignKey("users.id") but keeping loose for now to recognize existing data seamlessly
    # user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE")) 
    channel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
