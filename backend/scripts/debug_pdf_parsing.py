
import asyncio
import sys
import os
from sqlalchemy import select, text
from app.database import get_session_factory
from app.models import Act, Section

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def inspect_specific_sections():
    session_factory = get_session_factory()
    async with session_factory() as session:
        # List ALL Acts first
        res = await session.execute(select(Act).order_by(Act.id))
        all_acts = res.scalars().all()
        
        with open("parsing_debug.log", "w", encoding="utf-8") as f:
            f.write("--- ALL ACTS IN DB ---\n")
            for a in all_acts:
                f.write(f"ID: {a.id} | Name: {a.name} | Created: {a.id}\n")
            f.write("-" * 30 + "\n")

            # Find latest IPC or BNS
            # We want to check the *latest* ones if multiple exist
            target_acts = [a for a in all_acts if a.short_name in ['IPC', 'BNS']]
            
            for act in target_acts:
                f.write(f"\nEvaluating Act: {act.name} (ID: {act.id})\n")
                
                # Check how many sections exist
                count_res = await session.execute(text(f"SELECT count(*) FROM sections WHERE act_id = {act.id}"))
                count = count_res.scalar()
                f.write(f"Total Sections Found: {count}\n")
                
                # Retrieve first 5 sections to see how they look
                sections = await session.execute(
                    select(Section).where(Section.act_id == act.id).order_by(Section.id).limit(5)
                )
                
                f.write("--- First 5 Sections ---\n")
                for sec in sections.scalars().all():
                    f.write(f"Num: '{sec.section_number}' | Title: '{sec.title}'\n")
                    f.write(f"Content Preview: {sec.content[:200].replace(chr(10), ' ')}\n")
                    f.write("-" * 30 + "\n")
                
                # Check if Section 302 (for IPC) or 103 (for BNS) exists
                target_num = "302" if act.short_name == "IPC" else "103"
                f.write(f"\nLooking for Section {target_num}...\n")
                
                target_sec = await session.execute(
                    select(Section).where(Section.act_id == act.id, Section.section_number == target_num)
                )
                ts = target_sec.scalars().first()
                if ts:
                    f.write(f"✅ FOUND Section {target_num}!\n")
                    f.write(f"Title: {ts.title}\n")
                    f.write(f"Content: {ts.content[:500]}\n")
                else:
                    f.write(f"❌ MISSING Section {target_num}\n")
                    
                    # Try to find text "302" in ANY section content to see where it went
                    f.write(f"Searching for '{target_num}' in content...\n")
                    search_res = await session.execute(
                        select(Section).where(Section.act_id == act.id, Section.content.ilike(f"%Section {target_num}%")).limit(1)
                    )
                    found = search_res.scalars().first()
                    if found:
                        f.write(f"Found mention in Section {found.section_number}: {found.content[:200]}...\n")
                    else:
                        f.write("Not found in any content either.\n")

if __name__ == "__main__":
    try:
        asyncio.run(inspect_specific_sections())
    except Exception as e:
        import traceback
        with open("parsing_debug.log", "a") as f:
            f.write("\nCRASH:\n")
            f.write(traceback.format_exc())
        print(e)
