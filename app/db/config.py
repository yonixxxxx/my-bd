# from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
# from fastapi import Depends
# from typing import AsyncGenerator, Annotated
# from decouple import config
#
# DB_USER = config("DB_USER")
# DB_PASS = config("DB_PASS")
# DB_NAME = config("DB_NAME")
# DB_PORT = config("DB_PORT", cast=int)
# DB_HOST = config("DB_HOST")
#
# DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
#
#
# engine = create_async_engine(DATABASE_URL,echo=True,future=True)
#
# async_session = async_sessionmaker(bind=engine, expire_on_commit=False,class_=AsyncSession)
#
# async def get_session() -> AsyncGenerator[AsyncSession, None]:
#     async with async_session() as session:
#         yield session
#
# SessionDep = Annotated[AsyncSession, Depends(get_session)]

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from urllib.parse import quote_plus


DB_USER = "postgres"
DB_PASS = "kOIS+86Axn05+rZ"
DB_NAME = "fastapi_db"
DB_PORT = "5432"
DB_HOST = "localhost"

DB_PASS_ENCODED = quote_plus(DB_PASS)


DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


Base = declarative_base()


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


SessionDep = Annotated[AsyncSession, Depends(get_db)]