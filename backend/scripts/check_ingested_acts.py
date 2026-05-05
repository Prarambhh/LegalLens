import logging
import sys
import asyncio
from sqlalchemy import select, func
from app.database import get_session_factory
from app.models.sections import Section
from app.models.acts import Act

# Suppress logs
logging.basicConfig(level=logging.ERROR)
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

async def check_acts():
    factory = get_session_factory()
    async with factory() as session:
        stmt = select(Act.name, func.count(Section.id)).outerjoin(Section).group_by(Act.name)
        result = await session.execute(stmt)
        rows = result.all()
        
        print("\n--- Ingested Laws in Database ---")
        if not rows:
            print("No laws found in database (Database is empty).")
        else:
            for act_name, count in rows:
                print(f"• {act_name}: {count} sections")
        print("---------------------------------\n")

if __name__ == "__main__":
    asyncio.run(check_acts())
