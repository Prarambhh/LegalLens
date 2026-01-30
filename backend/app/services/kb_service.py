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
        
        # Convert type string to ActType enum
        act_type_str = act_metadata["type"]
        try:
            act_type = ActType(act_type_str)  # Try direct value match ("Central", "State")
        except ValueError:
            # Try uppercase match (CENTRAL, STATE)
            act_type = ActType[act_type_str.upper()]
        
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
        
        # Simple Section Parsing: Split by "Section X." or "Section X "
        # Relaxed Regex: Matches "Section 123", "Section. 123", "\nSection 123", "Article 123"
        # Handles case like "Section 103" where 103 is start of line or after space.
        # Added [\.] to start group to catch "end of sentence.Section 123"
        pattern = re.compile(r'(?:^|[\s\n\.]+)((?:Section|Article)\s*[\.]?\s+([A-Z0-9]+[A-Z]*))', re.IGNORECASE | re.MULTILINE)
        
        matches = list(pattern.finditer(text_content))
        
        sections_data = []
        if not matches:
            # Fallback: Treat whole doc as one big section or error?
            # Let's create one "Whole Act" section for now to allow RAG to work broadly
            sections_data.append({
                "number": "Full",
                "title": "Full Text",
                "content": text_content
            })
        else:
            for i in range(len(matches)):
                start = matches[i].start()
                # End is start of next match or end of string
                end = matches[i+1].start() if i + 1 < len(matches) else len(text_content)
                
                heading = matches[i].group(1) # "Section 123"
                sec_num = matches[i].group(2) # "123"
                
                content = text_content[start:end].strip()
                # Try to extract title (first line after Section X)
                lines = content.split('\n')
                title = lines[0] if lines else "Unknown"
                if title.lower().startswith("section"):
                     # Sometimes the title is on the next line
                     if len(lines) > 1:
                         title = lines[1].strip()
                
                sections_data.append({
                    "number": sec_num,
                    "title": title[:500],
                    "content": content
                })
        
        # Generate Embeddings and Save Sections
        for sec in sections_data:
            embedding = self.embedding_service.embed(sec["content"][:1000]) # Embed first 1000 chars or summary? 
            # Ideally embed chunk.
            
            new_section = Section(
                act_id=new_act.id,
                section_number=sec["number"],
                title=sec["title"],
                content=sec["content"],
                embedding=embedding
            )
            self.session.add(new_section)
        
        await self.session.commit()
        return {"id": new_act.id, "sections_count": len(sections_data)}

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
