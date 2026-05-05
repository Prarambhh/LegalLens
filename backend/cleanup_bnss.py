
import asyncio
from app.database import get_db
from sqlalchemy import text

async def cleanup_bnss():
    async for db in get_db():
        # Find BNSS (ID 26) - Hardcoded based on investigation
        act_id = 26
        
        print(f"Purging BNSS Act ID: {act_id}")
            
        # Delete Sections
        await db.execute(text("DELETE FROM sections WHERE act_id = :id"), {"id": act_id})
        # Delete Act
        await db.execute(text("DELETE FROM acts WHERE id = :id"), {"id": act_id})
        
        await db.commit()
        print("✅ Successfully deleted BNSS Act and Sections.")

if __name__ == "__main__":
    asyncio.run(cleanup_bnss())
