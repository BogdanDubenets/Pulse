
import asyncio
import ssl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from database.models import Channel

async def run():
    db_url = 'postgresql+asyncpg://postgres.irjqhaxbinyczgyfndzc:2WSG/?XynHg.?8x@aws-1-eu-west-1.pooler.supabase.com:6543/postgres'
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    engine = create_async_engine(db_url, connect_args={'ssl': ctx, 'prepared_statement_cache_size': 0, 'statement_cache_size': 0})
    Session = async_sessionmaker(engine, class_=AsyncSession)
    async with Session() as s:
        res = await s.execute(select(Channel).where(Channel.id == 14))
        c = res.scalar()
        if c:
            print(f'CHANNEL_DATA|{c.title}|{c.username}|{c.telegram_id}')
        else:
            print('CHANNEL_NOT_FOUND')

if __name__ == "__main__":
    asyncio.run(run())
