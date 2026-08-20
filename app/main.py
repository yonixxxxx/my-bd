from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


from app.db.config import engine, Base


from app.account.routers import router as account_router
from app.products.routers import router as product_router


import app.account.models
import app.products.models


@asynccontextmanager
async def lifespan(app: FastAPI):

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(" Таблицы базы данных созданы (если их не было). Приложение запущено")

    yield

    print(" Приложение завершает работу")



app = FastAPI(
    title="FastAPI Marketplace",
    description="Аутентификация, управление пользователями и товарами",
    version="1.0.0",
    lifespan=lifespan
)

# "http://localhost:5173",
# "http://localhost:5175",
# "http://localhost:5176",
# "http://localhost:5177",
# "http://localhost:5178",
# "http://localhost:3000"



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(account_router, prefix="/account", tags=["Account"])
app.include_router(product_router, tags=["Products"])


@app.get("/")
async def root():
    return {"message": "Добро пожаловать на FastAPI Marketplace"}