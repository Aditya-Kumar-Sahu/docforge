import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def run():
    url = os.getenv("DATABASE_URL").replace("+asyncpg", "")
    print(f"Connecting to {url}")
    try:
        conn = await asyncpg.connect(url)
        print("Connected successfully!")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
