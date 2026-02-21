import asyncio
from database.connection import AsyncSessionLocal
from sqlalchemy import select
from database.models import User

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        for user in users:
            print(f"User: {user.id} - {user.first_name} ({user.username})")

if __name__ == "__main__":
    asyncio.run(main())
