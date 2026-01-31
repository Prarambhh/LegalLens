"""
Search Service
Hybrid search combining vector similarity and keyword matching.
"""

from typing import List, Optional
from dataclasses import dataclass
from sqlalchemy import select, func, text, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Section, Act, CaseLaw
from app.services.embedding_service import get_embedding_service

# Map common legal terms to relevant IPC/BNS section numbers for boosted retrieval
# This ensures queries like "murder" or "robbery" return the correct sections
LEGAL_TERM_BOOST = {
    # Murder / Homicide
    "murder": ["302", "300", "299", "103", "101"],  # IPC 302, BNS 103
    "homicide": ["299", "300", "302", "101", "103"],
    "culpable homicide": ["299", "300", "101"],
    "death penalty": ["302", "303", "103"],
    
    # Robbery / Theft
    "robbery": ["390", "391", "392", "309"],  # IPC 390-392, BNS 309
    "theft": ["378", "379", "380", "303", "304"],  # IPC 378-380, BNS 303
    "dacoity": ["391", "395", "396", "310", "311"],  # IPC 391, 395-396
    
    # Assault / Hurt
    "assault": ["351", "352", "353", "130", "131", "132"],
    "grievous hurt": ["320", "325", "326", "117", "118"],
    "hurt": ["319", "321", "323", "324", "115", "116"],
    
    # Sexual Offences
    "rape": ["375", "376", "63", "64", "65"],  # IPC 375-376, BNS 63-65
    "sexual assault": ["354", "354A", "74", "75"],
    
    # Cheating / Fraud
    "cheating": ["415", "417", "420", "318", "319"],
    "fraud": ["415", "420", "318"],
    "forgery": ["463", "464", "465", "336", "337"],
    
    # Kidnapping
    "kidnapping": ["359", "360", "361", "137", "138"],
    "abduction": ["362", "363", "139", "140"],
    
    # Defamation
    "defamation": ["499", "500", "356"],
    
    # Criminal Intimidation
    "criminal intimidation": ["503", "506", "351"],
    "extortion": ["383", "384", "385", "306", "307"],
}


@dataclass
class SearchResult:
    """Represents a search result with relevance score."""
    section_id: int
    act_name: str
    act_short_name: Optional[str]
    section_number: str
    title: Optional[str]
    content: str
    chapter_number: Optional[str]
    similarity_score: float
    keyword_score: float = 0.0
    combined_score: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "section_id": self.section_id,
            "act_name": self.act_name,
            "act_short_name": self.act_short_name,
            "section_number": self.section_number,
            "title": self.title,
            "content": self.content,
            "chapter_number": self.chapter_number,
            "similarity_score": round(self.similarity_score, 4),
            "keyword_score": round(self.keyword_score, 4),
            "combined_score": round(self.combined_score, 4)
        }


class SearchService:
    """
    Hybrid search service combining:
    1. Semantic Search (pgvector cosine similarity)
    2. Keyword Search (PostgreSQL full-text search / ILIKE)
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.embedding_service = get_embedding_service()
    
    async def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        act_filter: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Perform semantic search using vector similarity.
        
        Args:
            query: User's search query
            top_k: Number of results to return
            act_filter: Optional filter by act short name (e.g., "BNS", "IPC")
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed(query)
        
        # Build query with cosine distance
        stmt = (
            select(
                Section.id,
                Section.section_number,
                Section.title,
                Section.content,
                Section.chapter_number,
                Act.name.label("act_name"),
                Act.short_name.label("act_short_name"),
                # Cosine similarity: 1 - cosine_distance
                (1 - Section.embedding.cosine_distance(query_embedding)).label("similarity")
            )
            .join(Act, Section.act_id == Act.id)
            .where(Section.embedding.isnot(None))
            .order_by(Section.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        
        # Apply act filter if specified
        if act_filter:
            stmt = stmt.where(
                or_(
                    Act.short_name.ilike(f"%{act_filter}%"),
                    Act.name.ilike(f"%{act_filter}%")
                )
            )
        
        result = await self.session.execute(stmt)
        rows = result.fetchall()
        
        return [
            SearchResult(
                section_id=row.id,
                act_name=row.act_name,
                act_short_name=row.act_short_name,
                section_number=row.section_number,
                title=row.title,
                content=row.content,
                chapter_number=row.chapter_number,
                similarity_score=float(row.similarity) if row.similarity else 0.0
            )
            for row in rows
        ]
    
    async def keyword_search(
        self,
        query: str,
        top_k: int = 5,
        act_filter: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Perform keyword search using ILIKE pattern matching.
        
        For production, consider using PostgreSQL full-text search (tsvector/tsquery)
        or an external search engine like Elasticsearch.
        """
        # Split query into keywords
        keywords = query.lower().split()
        
        # Build conditions for each keyword
        conditions = []
        for kw in keywords:
            pattern = f"%{kw}%"
            conditions.append(
                or_(
                    Section.content.ilike(pattern),
                    Section.title.ilike(pattern),
                    Section.section_number.ilike(pattern)
                )
            )
        
        stmt = (
            select(
                Section.id,
                Section.section_number,
                Section.title,
                Section.content,
                Section.chapter_number,
                Act.name.label("act_name"),
                Act.short_name.label("act_short_name"),
            )
            .join(Act, Section.act_id == Act.id)
            .where(*conditions)
            .limit(top_k)
        )
        
        if act_filter:
            stmt = stmt.where(
                or_(
                    Act.short_name.ilike(f"%{act_filter}%"),
                    Act.name.ilike(f"%{act_filter}%")
                )
            )
        
        result = await self.session.execute(stmt)
        rows = result.fetchall()
        
        return [
            SearchResult(
                section_id=row.id,
                act_name=row.act_name,
                act_short_name=row.act_short_name,
                section_number=row.section_number,
                title=row.title,
                content=row.content,
                chapter_number=row.chapter_number,
                similarity_score=0.0,
                keyword_score=1.0  # Binary match for now
            )
            for row in rows
        ]
    
    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        act_filter: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Combine semantic and keyword search with weighted ranking.
        
        Args:
            query: User's search query
            top_k: Final number of results
            semantic_weight: Weight for semantic similarity (0-1)
            keyword_weight: Weight for keyword matching (0-1)
            act_filter: Optional filter by act name
        """
        # Get more results from each search for re-ranking
        fetch_k = top_k * 2
        
        # Perform both searches
        semantic_results = await self.semantic_search(query, fetch_k, act_filter)
        keyword_results = await self.keyword_search(query, fetch_k, act_filter)
        
        # Create a map for combining scores
        results_map = {}
        
        # Add semantic results
        for r in semantic_results:
            results_map[r.section_id] = r
            r.combined_score = r.similarity_score * semantic_weight
        
        # Merge keyword results
        for r in keyword_results:
            if r.section_id in results_map:
                # Update existing result with keyword score
                existing = results_map[r.section_id]
                existing.keyword_score = r.keyword_score
                existing.combined_score += r.keyword_score * keyword_weight
            else:
                # Add new result from keyword search
                r.combined_score = r.keyword_score * keyword_weight
                results_map[r.section_id] = r
        
        # --- LEGAL TERM BOOSTING ---
        # Check if query contains any legal terms that should force-include specific sections
        query_lower = query.lower()
        boosted_sections = set()
        for term, section_numbers in LEGAL_TERM_BOOST.items():
            if term in query_lower:
                boosted_sections.update(section_numbers)
        
        # Fetch boosted sections directly from database
        if boosted_sections:
            boost_conditions = [Section.section_number.in_(list(boosted_sections))]
            if act_filter:
                boost_conditions.append(
                    or_(
                        Act.short_name.ilike(f"%{act_filter}%"),
                        Act.name.ilike(f"%{act_filter}%")
                    )
                )
            
            stmt = (
                select(
                    Section.id,
                    Section.section_number,
                    Section.title,
                    Section.content,
                    Section.chapter_number,
                    Act.name.label("act_name"),
                    Act.short_name.label("act_short_name"),
                )
                .join(Act, Section.act_id == Act.id)
                .where(*boost_conditions)
                .limit(10)  # Limit boosted sections
            )
            
            result = await self.session.execute(stmt)
            rows = result.fetchall()
            
            # Add boosted sections with high priority score
            for row in rows:
                if row.id not in results_map:
                    boosted_result = SearchResult(
                        section_id=row.id,
                        act_name=row.act_name,
                        act_short_name=row.act_short_name,
                        section_number=row.section_number,
                        title=row.title,
                        content=row.content,
                        chapter_number=row.chapter_number,
                        similarity_score=0.8,  # High base score for boosted
                        keyword_score=1.0,
                        combined_score=1.5  # Ensure boosted sections appear first
                    )
                    results_map[row.id] = boosted_result
                else:
                    # Boost existing result's score
                    results_map[row.id].combined_score += 0.5
        # --- END LEGAL TERM BOOSTING ---
        
        # Sort by combined score and return top_k
        sorted_results = sorted(
            results_map.values(),
            key=lambda x: x.combined_score,
            reverse=True
        )
        
        return sorted_results[:top_k]

    async def search_case_laws(
        self,
        query: str,
        top_k: int = 3
    ) -> List[SearchResult]:
        """Search for relevant case laws using vector similarity."""
        query_embedding = self.embedding_service.embed(query)
        
        stmt = (
            select(
                CaseLaw.id,
                CaseLaw.title,
                CaseLaw.content,
                CaseLaw.court_name,
                CaseLaw.judgment_date,
                (1 - CaseLaw.embedding.cosine_distance(query_embedding)).label("similarity")
            )
            .where(CaseLaw.embedding.isnot(None))
            .order_by(CaseLaw.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        
        result = await self.session.execute(stmt)
        rows = result.fetchall()
        
        return [
            SearchResult(
                section_id=row.id,
                act_name=row.court_name or "Unknown Court",
                act_short_name="CASE",
                section_number="N/A",
                title=row.title,
                content=row.content,
                chapter_number=str(row.judgment_date) if row.judgment_date else None,
                similarity_score=float(row.similarity) if row.similarity else 0.0
            )
            for row in rows
        ]
