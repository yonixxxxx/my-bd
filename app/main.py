from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.db.table_bd import init_db
from app.account.routers import router as account_router
from app.products.routers import router as product_router
import app.account.models
import app.products.models



@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("Запуск приложения")
    yield
    print("Завершение работы приложения")


app = FastAPI(
    title="FastAPI Marketplace",
    description="Аутентификация, управление пользователями и товарами",
    version="1.0.0",
    lifespan=lifespan
)


app.include_router(account_router, prefix="/account", tags=["Account"])
app.include_router(product_router, prefix="/products", tags=["Products"])


@app.get("/")
async def root():
    return {"message": "Добро пожаловать на FastAPI Marketplace"}