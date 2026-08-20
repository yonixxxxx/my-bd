import asyncio
from app.db.config import engine, Base
from app.account import models as account_models
from app.products import models as product_models

async def reset_database():
    async with engine.begin() as conn:
        print(" Удаление всех таблиц...")
        await conn.run_sync(Base.metadata.drop_all)
        print(" Создание таблиц заново...")
        await conn.run_sync(Base.metadata.create_all)
    print(" База данных успешно пересоздана! (колонка location добавлена)")

if __name__ == "__main__":
    print(" ВНИМАНИЕ: Это действие удалит ВСЕ данные из базы!")
    confirm = input("Вы уверены, что хотите продолжить? (y/N): ")
    if confirm.lower() == "y":
        asyncio.run(reset_database())
    else:
        print(" Отменено.")