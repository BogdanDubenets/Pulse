
import asyncio
import ssl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, selectinload
from sqlalchemy import BigInteger, String, Integer, ForeignKey

# Спеціально для діагностику без завантаження всього проекту
class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str] = mapped_column(String)
    username: Mapped[str] = mapped_column(String)

class Channel(Base):
    __tablename__ = "channels"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"))
    channel = relationship("Channel")

async def main():
    db_url = "postgresql+asyncpg://postgres.irjqhaxbinyczgyfndzc:2WSG/?XynHg.?8x@aws-1-eu-west-1.pooler.supabase.com:6543/postgres"
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    engine = create_async_engine(
        db_url,
        connect_args={
            "ssl": ctx,
            "prepared_statement_cache_size": 0,
            "statement_cache_size": 0
        }
    )
    
    Session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with Session() as session:
        print("--- USERS ---")
        users = (await session.execute(select(User))).scalars().all()
        for u in users:
            print(f"User: {u.id} | {u.first_name} (@{u.username})")
        
        print("\n--- SUBSCRIPTIONS ---")
        subs = (await session.execute(select(UserSubscription).options(selectinload(UserSubscription.channel)))).scalars().all()
        for s in subs:
            print(f"User {s.user_id} -> {s.channel.title if s.channel else s.channel_id}")

if __name__ == "__main__":
    asyncio.run(main())
