import asyncio
import asyncpg
import os
from dotenv import load_dotenv


load_dotenv()


DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "12345678")
DB_NAME = os.getenv("DB_NAME", "fastapi_db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_HOST = os.getenv("DB_HOST", "localhost")


async def create_database():
    try:

        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database="postgres"
        )


        result = await conn.fetch(
            "SELECT 1 FROM pg_database WHERE datname = $1", DB_NAME
        )

        if not result:
            await conn.execute(f'CREATE DATABASE "{DB_NAME}"')
            print(f" База данных {DB_NAME} успешно создана!")
        else:
            print(f"ℹ База данных {DB_NAME} уже существует.")

        await conn.close()

    except Exception as e:
        print(f" Ошибка при создании базы данных: {e}")


if __name__ == "__main__":
    asyncio.run(create_database())