import asyncio
from app.db.config import engine, Base
from app.account import models

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы базы данных успешно созданы")

if __name__ == "__main__":
    asyncio.run(init_db())