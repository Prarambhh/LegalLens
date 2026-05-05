
import asyncio
from app.database import get_db
from sqlalchemy import text

async def list_acts():
    async for db in get_db():
        result = await db.execute(text("SELECT id, name, type FROM acts"))
        rows = result.fetchall()
        print(f"{'ID':<5} {'Name':<40} {'Type':<10}")
        print("-" * 60)
        for row in rows:
            print(f"{row.id:<5} {row.name:<40} {row.type:<10}")

if __name__ == "__main__":
    asyncio.run(list_acts())
