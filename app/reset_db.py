import asyncio
from app.db.config import engine, Base
from app.account import models



async def reset_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("Все таблицы удалены")
        await conn.run_sync(Base.metadata.create_all)
        print("Таблицы созданы заново")


if __name__ == "__main__":
    asyncio.run(reset_database())