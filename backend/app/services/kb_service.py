"""
Knowledge Base Service
Handles ingestion of legal documents (Acts, Case Laws) into the system.
"""
import re
import io
import PyPDF2
from docx import Document as DocxDocument
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any

from app.models import Act, Section, CaseLaw
from app.models.acts import ActType
from app.services.embedding_service import get_embedding_service

class KnowledgeBaseService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.embedding_service = get_embedding_service()

    async def _parse_text(self, file: UploadFile) -> str:
        """Extract text from PDF/DOCX/TXT."""
        content = await file.read()
        file_ext = file.filename.split('.')[-1].lower()
        text = ""

        try:
            if file_ext == 'pdf':
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            elif file_ext in ['docx', 'doc']:
                doc = DocxDocument(io.BytesIO(content))
                for para in doc.paragraphs:
                    text += para.text + "\n"
            elif file_ext == 'txt':
                text = content.decode('utf-8')
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format.")
            return text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error parsing file: {e}")

    async def add_act(self, file: UploadFile, act_metadata: Dict[str, Any]):
        """
        Add a new Act to the DB.
        Expects metadata: name, year, type, short_name.
        Tries to parse sections from the text.
        """
        text_content = await self._parse_text(file)
        
        # Save to file for debugging
        with open("e:/LegalLens/backend/debug_pdf_text.txt", "w", encoding="utf-8") as f:
            f.write(text_content)
            
        print("\n\n=== PDF TEXT CONTENT PREVIEW (START) ===")
        print(text_content[:2000])
        print("=== PDF TEXT CONTENT PREVIEW (END) ===\n\n")
        
        # Convert type string to ActType enum
        act_type_str = act_metadata["type"]
        try:
            act_type = ActType(act_type_str)  # Try direct value match ("Central", "State")
        except ValueError:
            # Try uppercase match (CENTRAL, STATE)
            act_type = ActType[act_type_str.upper()]
        
        # Check if Act already exists
        from sqlalchemy import select
        result = await self.session.execute(select(Act).where(Act.name == act_metadata["name"]))
        existing_act = result.scalar_one_or_none()
        
        if existing_act:
            new_act = existing_act
            # Update metadata if needed, or just use existing
            print(f"Act '{new_act.name}' already exists. Adding sections to it.")
        else:
            # Create Act record
            new_act = Act(
                name=act_metadata["name"],
                year=act_metadata["year"],
                type=act_type,
                short_name=act_metadata.get("short_name"),
                description=act_metadata.get("description")
            )
            self.session.add(new_act)
            await self.session.flush() # Get ID
        
        # Improved Section Parsing
        # Pattern 1: "Section 123" or "Article 123"
        # Pattern 2: "123." at start of line (common in gazettes)
        # Regex Explanation:
        # (?:^|[\n]) -> Start of line
        # (?:Section|Article)?\s* -> Optional "Section" or "Article"
        # (\d+[A-Z]*)\. -> Group 1: The Number (e.g. 1, 302, 376A) followed by dot
        # \s+([^\n]+) -> Group 2: The Title (rest of the line)
        # Improved Section Parsing
        # Flexible Regex for various legal document formats
        # 1. "Section 123"
        # 2. "Article 123"
        # 3. "123." at start of line
        # 4. "123 " at start of line (rare but happens)
        
        # Improved Section Parsing (Final Robust Version)
        # Handles "Section 123", "123.", "123.Content", "123.(1)"
        pattern = re.compile(
            r'(?:^|[\n])'                  # Start of line
            r'(?:(?:Section|Article)\s+)?' # Optional prefix
            r'(\d+[A-Z]*)\.'               # digits + optional letters + DOT (Mandatory dot if just number)
            r'\s*'                         # Optional Space (handles "2.In")
            r'([^\n]+(?:$|[\n]))',         # Capture rest of line (Title or Start of content)
            re.IGNORECASE | re.MULTILINE
        )
        
        all_matches = list(pattern.finditer(text_content))
        
        sections_data = []
        
        # Deduplication and Construction
        if not all_matches:
             sections_data.append({
                "number": "Full",
                "title": "Full Document",
                "content": text_content
            })
        else:
            for i in range(len(all_matches)):
                start = all_matches[i].start()
                end = all_matches[i+1].start() if i + 1 < len(all_matches) else len(text_content)
                
                m = all_matches[i]
                sec_num = m.group(1).strip()
                # If group 2 looks like content (e.g. starts with "(" or lower case or is very long), 
                # use generic title
                captured_text = m.group(2).strip()
                
                # Heuristic for title:
                # If text starts with ( or has > 100 chars, it's probably content, not a title.
                # But in this PDF, title is MISSING or interleaved. 
                # So we just use "Section X" + first few words as title.
                title = f"Section {sec_num}"
                if len(captured_text) < 100 and not captured_text.startswith("("):
                     title += f": {captured_text}"
                
                content = text_content[start:end].strip()
                
                sections_data.append({
                    "number": sec_num,
                    "title": title,
                    "content": content
                })
        
        # Deduplication using "Longest Content Wins" strategy
        # This handles Table of Contents (TOC) entries appearing before real sections.
        # TOC entries are short ("123. Title ... 45"), Real sections are long.
        
        candidates = {} # Map section_number -> list of section dicts
        for sec in sections_data:
            num = sec["number"]
            if num not in candidates:
                candidates[num] = []
            candidates[num].append(sec)
            
        final_sections = []
        for num, variants in candidates.items():
            # Pick the variant with longest content length
            # But unlikely to be > 10000 if it's just a repetition? 
            # Real section is likely the longest.
            best_variant = max(variants, key=lambda x: len(x["content"]))
            final_sections.append(best_variant)

        # DB Deduplication: Get existing section numbers in DB
        from sqlalchemy import select
        result = await self.session.execute(select(Section.section_number).where(Section.act_id == new_act.id))
        existing_numbers = {row[0] for row in result.all()}
        
        # Generate Embeddings and Save Sections (Only new ones from our best candidates)
        count = 0
        for sec in final_sections:
            if sec["number"] in existing_numbers:
                continue # Skip if already in DB (assuming user wants to keep old data? Or overwrite?)
                # If we are fixing corruption, we might want to OVERWRITE?
                # But 'existing_numbers' check prevents overwrite.
                # User needs to DELETE Act first or we should change logic to update?
                # For now, let's assume CLEAN database or new Act name.

                
            embedding = self.embedding_service.embed(sec["content"][:1000])
            
            new_section = Section(
                act_id=new_act.id,
                section_number=sec["number"],
                title=sec["title"],
                content=sec["content"],
                embedding=embedding
            )
            self.session.add(new_section)
            count += 1
        
        if count > 0:
            await self.session.commit()
            print(f"Added {count} new sections to {new_act.name}")
        else:
            print(f"No new sections found for {new_act.name}")
            
        return {"id": new_act.id, "sections_count": count, "total_scanned": len(sections_data)}

    async def add_case_law(self, file: UploadFile, metadata: Dict[str, Any]):
        """
        Add a Case Law judgment.
        Expects metadata: title, court_name, date.
        """
        text_content = await self._parse_text(file)
        
        # Embed the content (or headnotes search)
        # Using a simple truncation for embedding logic
        embedding = self.embedding_service.embed(text_content[:2000])
        
        new_case = CaseLaw(
            title=metadata["title"],
            court_name=metadata.get("court_name", "Unknown Court"),
            content=text_content,
            judgment_date=metadata.get("judgment_date"), # Should be date obj or None
            citation=metadata.get("citation"),
            embedding=embedding
        )
        self.session.add(new_case)
        await self.session.commit()
        return {"id": new_case.id, "title": new_case.title}
