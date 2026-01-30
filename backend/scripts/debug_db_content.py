
import asyncio
import sys
import os
from sqlalchemy import select, func
from app.database import get_session_factory
from app.models import Act, Section

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def check_key_sections():
    session_factory = get_session_factory()
    async with session_factory() as session:
        # Check Total Counts
        print("--- Act Section Counts ---")
        acts = await session.execute(select(Act))
        for act in acts.scalars():
            count = await session.scalar(select(func.count(Section.id)).where(Section.act_id == act.id))
            print(f"Act: {act.name} ({act.short_name}) - Sections: {count}")
        
        # Check for specific "Murder" sections
        print("\n--- Searching for Murder Sections ---")
        
        # IPC 302
        ipc_302 = await session.execute(
            select(Section).join(Act).where(
                Act.short_name == 'IPC',
                Section.section_number.ilike('%302%')
            )
        )
        found_ipc = ipc_302.scalars().all()
        if found_ipc:
            print(f"✅ Found IPC 302 candidates: {len(found_ipc)}")
            for s in found_ipc:
                print(f"   - {s.section_number}: {s.content[:100]}...")
        else:
            print("❌ IPC Section 302 NOT FOUND")

        # BNS 103
        bns_103 = await session.execute(
            select(Section).join(Act).where(
                Act.short_name == 'BNS',
                Section.section_number.ilike('%103%')
            )
        )
        found_bns = bns_103.scalars().all()
        if found_bns:
            print(f"✅ Found BNS 103 candidates: {len(found_bns)}")
            for s in found_bns:
                print(f"   - {s.section_number}: {s.content[:100]}...")
        else:
            print("❌ BNS Section 103 NOT FOUND")

if __name__ == "__main__":
    asyncio.run(check_key_sections())
