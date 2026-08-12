import asyncio
import asyncpg


async def create_database():
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="kOIS+86Axn05+rZ",
            database="postgres"
        )

        result = await conn.fetch("SELECT 1 FROM pg_database WHERE datname = 'fastapi_db'")

        if not result:
            await conn.execute('CREATE DATABASE "fastapi_db"')
            print(" База данных fastapi_db создана!")
        else:
            print(" База данных fastapi_db уже существует")

        await conn.close()

    except Exception as e:
        print(f" Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(create_database())