
import asyncio
from app.database import get_db
from sqlalchemy import text

async def check_bnss_counts():
    async for db in get_db():
        # Check counts for BNSS (ID 26) Section 302 and 300
        print("--- BNSS (ID 26) Duplicate Check ---")
        
        result = await db.execute(text(
            "SELECT section_number, COUNT(*) as cnt "
            "FROM sections "
            "WHERE act_id = 26 AND section_number IN ('302', '300') "
            "GROUP BY section_number"
        ))
        rows = result.fetchall()
        for row in rows:
            print(f"Section {row.section_number}: {row.cnt} copies")
            
        # Inspect Content of copies
        result = await db.execute(text(
            "SELECT section_number, title, length(content) "
            "FROM sections "
            "WHERE act_id = 26 AND section_number = '302'"
        ))
        rows = result.fetchall()
        print("\n--- Details for Section 302 ---")
        for row in rows:
            print(f"{row.section_number} | {row.title[:30]} | Len: {row.length}")

if __name__ == "__main__":
    asyncio.run(check_bnss_counts())
