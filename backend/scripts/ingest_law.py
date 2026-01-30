#!/usr/bin/env python3
"""
LegalLens - Legal Document Ingestion Script
============================================

Ingests legal documents (JSON/PDF) into the database with:
- Section-based chunking (never breaks mid-sentence)
- HuggingFace embedding generation
- Batch database insertion

Usage:
    python ingest_law.py --input ../data/sample_bns.json
    python ingest_law.py --input ../data/sample_bns.json --dry-run
    python ingest_law.py --input document.pdf --format pdf
"""

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import AsyncSessionLocal, init_db
from app.models import Act, Section
from app.models.acts import ActType


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ParsedSection:
    """Represents a parsed section from a legal document."""
    chapter_number: Optional[str]
    chapter_title: Optional[str]
    section_number: str
    title: Optional[str]
    content: str
    keywords: Optional[str] = None


@dataclass
class ParsedAct:
    """Represents a parsed legal act."""
    name: str
    short_name: Optional[str]
    year: int
    act_type: ActType
    description: Optional[str]
    sections: List[ParsedSection]


# ============================================================================
# Embedding Service
# ============================================================================

class EmbeddingService:
    """Generates embeddings using HuggingFace sentence-transformers."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        print(f"📦 Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"✅ Model loaded. Embedding dimension: {self.dimension}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches."""
        embeddings = self.model.encode(
            texts, 
            batch_size=batch_size, 
            show_progress_bar=True,
            convert_to_numpy=True
        )
        return [emb.tolist() for emb in embeddings]


# ============================================================================
# Document Parsers
# ============================================================================

class LegalDocumentParser:
    """Base class for parsing legal documents."""
    
    # Common section patterns in Indian legal documents
    SECTION_PATTERNS = [
        # "Section 302." or "302."
        r'^(?:Section\s+)?(\d+[A-Z]?)\.\s*[-–—]?\s*(.+?)(?:\.|$)',
        # "(1) Some text" - subsection
        r'^\((\d+)\)\s*(.+)',
        # "1. Some text" - numbered list
        r'^(\d+)\.\s+(.+)',
    ]
    
    def parse(self, content: Any) -> ParsedAct:
        """Parse document and return structured data. Override in subclasses."""
        raise NotImplementedError


class JSONParser(LegalDocumentParser):
    """Parses JSON-formatted legal documents."""
    
    def parse(self, file_path: Path) -> ParsedAct:
        """
        Parse a JSON file containing legal act data.
        
        Expected JSON structure:
        {
            "act_name": "Bharatiya Nyaya Sanhita, 2023",
            "short_name": "BNS",
            "year": 2023,
            "type": "Central",
            "description": "...",
            "sections": [
                {
                    "chapter": "I",
                    "chapter_title": "Preliminary",
                    "section_number": "1",
                    "title": "Short title...",
                    "content": "Full text..."
                }
            ]
        }
        """
        print(f"📄 Parsing JSON file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Parse act type
        act_type_str = data.get('type', 'Central')
        act_type = ActType.CENTRAL if act_type_str == 'Central' else ActType.STATE
        
        # Parse sections
        sections = []
        for sec_data in data.get('sections', []):
            section = ParsedSection(
                chapter_number=str(sec_data.get('chapter', '')) or None,
                chapter_title=sec_data.get('chapter_title'),
                section_number=str(sec_data['section_number']),
                title=sec_data.get('title'),
                content=sec_data['content'],
                keywords=sec_data.get('keywords')
            )
            sections.append(section)
        
        return ParsedAct(
            name=data['act_name'],
            short_name=data.get('short_name'),
            year=data['year'],
            act_type=act_type,
            description=data.get('description'),
            sections=sections
        )


class PDFParser(LegalDocumentParser):
    """Parses PDF legal documents with section-based chunking."""
    
    def __init__(self):
        try:
            from PyPDF2 import PdfReader
            self.PdfReader = PdfReader
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF parsing. Install with: pip install pypdf2")
    
    def parse(self, file_path: Path, act_name: str, year: int, act_type: ActType = ActType.CENTRAL) -> ParsedAct:
        """
        Parse a PDF file and extract sections.
        
        Uses regex patterns to identify section boundaries.
        Never breaks mid-sentence - each section is complete.
        """
        print(f"📄 Parsing PDF file: {file_path}")
        
        # Extract all text from PDF
        reader = self.PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
        
        # Parse sections from text
        sections = self._extract_sections(full_text)
        
        return ParsedAct(
            name=act_name,
            short_name=None,
            year=year,
            act_type=act_type,
            description=None,
            sections=sections
        )
    
    def _extract_sections(self, text: str) -> List[ParsedSection]:
        """
        Extract sections from raw text using pattern matching.
        
        Strategy:
        1. Find all section headers (e.g., "Section 302.")
        2. Extract content between headers
        3. Ensure each chunk is a complete section (no mid-sentence breaks)
        """
        sections = []
        
        # Pattern to match section headers
        # Matches: "Section 1." or "1." or "Section 302A."
        section_header_pattern = r'(?:Section\s+)?(\d+[A-Z]?)\.\s*[-–—]?\s*([^\n]+)'
        
        # Find all section matches
        matches = list(re.finditer(section_header_pattern, text, re.MULTILINE))
        
        if not matches:
            print("⚠️  No sections found in document. Treating entire document as one section.")
            sections.append(ParsedSection(
                chapter_number=None,
                chapter_title=None,
                section_number="1",
                title="Full Document",
                content=text.strip()
            ))
            return sections
        
        # Extract each section's content
        for i, match in enumerate(matches):
            section_number = match.group(1)
            title = match.group(2).strip()
            
            # Content starts after the title
            content_start = match.end()
            
            # Content ends at the next section or end of document
            if i + 1 < len(matches):
                content_end = matches[i + 1].start()
            else:
                content_end = len(text)
            
            content = text[content_start:content_end].strip()
            
            # Ensure we don't break mid-sentence
            content = self._ensure_complete_sentences(content)
            
            sections.append(ParsedSection(
                chapter_number=None,  # Chapter detection would require more parsing
                chapter_title=None,
                section_number=section_number,
                title=title,
                content=content
            ))
        
        print(f"✅ Extracted {len(sections)} sections from PDF")
        return sections
    
    def _ensure_complete_sentences(self, text: str) -> str:
        """
        Ensure text ends with a complete sentence.
        Trims trailing incomplete sentences.
        """
        text = text.strip()
        if not text:
            return text
        
        # Find the last sentence-ending punctuation
        last_period = max(
            text.rfind('.'),
            text.rfind('?'),
            text.rfind('!')
        )
        
        if last_period > 0 and last_period < len(text) - 1:
            # Check if there's significant text after the last period
            remaining = text[last_period + 1:].strip()
            # If remaining text looks like a partial sentence, trim it
            if len(remaining) > 10 and not remaining[0].isupper():
                text = text[:last_period + 1]
        
        return text


# ============================================================================
# Database Operations
# ============================================================================

async def get_or_create_act(session: AsyncSession, parsed_act: ParsedAct) -> Act:
    """Get existing act or create new one."""
    # Check if act exists
    result = await session.execute(
        select(Act).where(Act.name == parsed_act.name)
    )
    act = result.scalar_one_or_none()
    
    if act:
        print(f"📚 Found existing act: {act.name}")
        return act
    
    # Create new act
    act = Act(
        name=parsed_act.name,
        short_name=parsed_act.short_name,
        year=parsed_act.year,
        type=parsed_act.act_type,
        description=parsed_act.description
    )
    session.add(act)
    await session.flush()  # Get the ID
    print(f"📚 Created new act: {act.name} (ID: {act.id})")
    return act


async def insert_sections(
    session: AsyncSession, 
    act: Act, 
    sections: List[ParsedSection],
    embeddings: List[List[float]]
) -> int:
    """Insert sections with embeddings into database."""
    count = 0
    for section, embedding in zip(sections, embeddings):
        db_section = Section(
            act_id=act.id,
            chapter_number=section.chapter_number,
            chapter_title=section.chapter_title,
            section_number=section.section_number,
            title=section.title,
            content=section.content,
            embedding=embedding,
            keywords=section.keywords
        )
        session.add(db_section)
        count += 1
    
    await session.commit()
    return count


# ============================================================================
# Main Ingestion Logic
# ============================================================================

async def ingest_document(
    file_path: Path,
    file_format: str = "json",
    dry_run: bool = False,
    act_name: Optional[str] = None,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Main ingestion function.
    
    Args:
        file_path: Path to the document file
        file_format: "json" or "pdf"
        dry_run: If True, parse but don't write to database
        act_name: Required for PDF files
        year: Required for PDF files
    
    Returns:
        Summary of ingestion results
    """
    print("=" * 60)
    print("🚀 LegalLens Document Ingestion")
    print("=" * 60)
    
    # Initialize embedding service
    settings = get_settings()
    embedding_service = EmbeddingService(settings.embedding_model)
    
    # Parse document
    if file_format == "json":
        parser = JSONParser()
        parsed_act = parser.parse(file_path)
    elif file_format == "pdf":
        if not act_name or not year:
            raise ValueError("act_name and year are required for PDF parsing")
        parser = PDFParser()
        parsed_act = parser.parse(file_path, act_name, year)
    else:
        raise ValueError(f"Unsupported format: {file_format}")
    
    print(f"\n📋 Parsed Act: {parsed_act.name}")
    print(f"   Year: {parsed_act.year}")
    print(f"   Type: {parsed_act.act_type.value}")
    print(f"   Sections: {len(parsed_act.sections)}")
    
    # Generate embeddings
    print("\n🔄 Generating embeddings...")
    section_texts = [
        f"{s.title or ''}\n{s.content}" 
        for s in parsed_act.sections
    ]
    embeddings = embedding_service.generate_embeddings_batch(section_texts)
    print(f"✅ Generated {len(embeddings)} embeddings")
    
    if dry_run:
        print("\n🔍 DRY RUN - No database changes made")
        print("\nSample sections:")
        for i, section in enumerate(parsed_act.sections[:3]):
            print(f"\n  Section {section.section_number}: {section.title}")
            print(f"    Content preview: {section.content[:100]}...")
            print(f"    Embedding dims: {len(embeddings[i])}")
        
        return {
            "status": "dry_run",
            "act_name": parsed_act.name,
            "sections_parsed": len(parsed_act.sections),
            "embeddings_generated": len(embeddings)
        }
    
    # Initialize database
    print("\n💾 Connecting to database...")
    await init_db()
    
    async with AsyncSessionLocal() as session:
        # Create or get act
        act = await get_or_create_act(session, parsed_act)
        
        # Insert sections
        print("\n📝 Inserting sections...")
        count = await insert_sections(session, act, parsed_act.sections, embeddings)
        print(f"✅ Inserted {count} sections")
    
    return {
        "status": "success",
        "act_name": parsed_act.name,
        "act_id": act.id,
        "sections_inserted": count
    }


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Ingest legal documents into LegalLens database"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to input file (JSON or PDF)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "pdf"],
        default="json",
        help="Input file format (default: json)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and generate embeddings but don't write to database"
    )
    parser.add_argument(
        "--act-name",
        help="Act name (required for PDF format)"
    )
    parser.add_argument(
        "--year",
        type=int,
        help="Act year (required for PDF format)"
    )
    
    args = parser.parse_args()
    
    file_path = Path(args.input)
    if not file_path.exists():
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)
    
    # Run ingestion
    result = asyncio.run(ingest_document(
        file_path=file_path,
        file_format=args.format,
        dry_run=args.dry_run,
        act_name=args.act_name,
        year=args.year
    ))
    
    print("\n" + "=" * 60)
    print("📊 Ingestion Summary")
    print("=" * 60)
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
