
import asyncio
import sys
import os
import io
import PyPDF2

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def debug_pdf_text(filename, search_terms):
    file_path = f"../../../{filename}" # Assuming running from backend/scripts, need to find where user keeps files or upload them again? 
    # Actually, we can't easily access the user's uploaded file unless we saved it.
    # But wait, the previous upload saved files to temp or DB? KService reads from UploadFile.
    
    # HACK: I will ignore the file path for now and ask the user to upload a single file to a debug endpoint I will create.
    # OR, better: I will inspect the logs of what `_parse_text` produced if I can instrument it.
    
    # Actually, I can write a small script that uses the SAME logic as kb_service but just prints.
    # But I need the PDF file.
    pass

# Strategy change: The user has the files. I can't read them from their machine.
# I will modify kb_service.py to LOG/PRINT the context around specific regex failures or just sample text.
# BUT, debugging via re-upload is slow.

# Alternative: I can add a temporary GET endpoint that dumps the raw text of the first few 1000 chars of a specific Act from the DB
# (Wait, we stored sections, but if section parsing failed, we likely have a "Full" section with the whole content?
# My code was:
# if not matches: sections_data.append({"number": "Full", ...})
# This means if regex failed completely, we should have 1 section with ALL text.
# Let's check if there is a section called "Full" for IPC in the DB.

from app.database import get_session_factory
from sqlalchemy import select
from app.models import Act, Section

async def check_full_content():
    session_factory = get_session_factory()
    async with session_factory() as session:
        # Check IPC
        ipc = await session.execute(select(Act).where(Act.short_name == 'IPC'))
        ipc_act = ipc.scalars().first()
        if not ipc_act:
            print("IPC Act not found")
            return

        # Find section "Full" or typical sections
        sections = await session.execute(select(Section).where(Section.act_id == ipc_act.id))
        all_sections = sections.scalars().all()
        
        print(f"IPC Sections Found: {len(all_sections)}")
        
        # Check if we have a "Full" section
        for s in all_sections:
            if s.section_number == "Full":
                print("⚠️ Found 'Full' section - Regex failed completely!")
                print(f"Sample content: {s.content[:500]}")
                # Search for 302 in this blob
                idx = s.content.find("302")
                if idx != -1:
                    print(f"\nCTX around 302:\n{s.content[idx-50:idx+50]}")
                return
            
            # If we have normal sections, let's see why 302 is missing.
            # Maybe it's inside another section?
            # Let's check a section closest to 300
            if "300" in s.section_number:
                 print(f"Found nearby section {s.section_number}: {s.content[:100]}...")

        # Brute force search for 302 in ALL sections
        print("\nSearching for '302' in ANY IPC section content...")
        found = False
        for s in all_sections:
            if "302" in s.content:
                print(f"Found '302' inside Section {s.section_number}!")
                idx = s.content.find("302")
                print(f"CTX: {s.content[idx-50:idx+50]}")
                found = True
                break
        
        if not found:
            print("❌ '302' text LITERALLY NOT FOUND in any extracted IPC text. PDF Parsing might be skipping pages?")

if __name__ == "__main__":
    asyncio.run(check_full_content())
