"""
CaseLaw Model
Represents court judgments and case law for legal research.
"""

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Index
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.database import Base
from app.config import get_settings

settings = get_settings()

# Embedding dimension: 384 for sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIM = settings.embedding_dimension


class CaseLaw(Base):
    """
    Court judgment/case law model.
    
    Used for RAG to provide case law references in legal research.
    """
    __tablename__ = "case_law"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Case identification
    title = Column(String(500), nullable=False)  # e.g., "State of Maharashtra v. XYZ"
    citation = Column(String(200), nullable=True)  # e.g., "(2023) 5 SCC 123"
    case_number = Column(String(100), nullable=True)  # e.g., "Criminal Appeal No. 123/2023"
    
    # Court details
    court_name = Column(String(200), nullable=False)  # e.g., "Supreme Court of India"
    bench = Column(String(500), nullable=True)  # Judges who heard the case
    
    # Dates
    judgment_date = Column(Date, nullable=True)
    
    # Content
    content = Column(Text, nullable=False)  # Full judgment text or summary
    headnotes = Column(Text, nullable=True)  # Key points/summary
    
    # Vector embedding for semantic search
    embedding = Column(Vector(EMBEDDING_DIM), nullable=True)
    
    # Metadata
    keywords = Column(String(500), nullable=True)  # Comma-separated keywords
    relevant_sections = Column(String(500), nullable=True)  # Related section numbers
    source_url = Column(String(1000), nullable=True)  # Link to original source
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index("ix_case_law_court", "court_name"),
        Index("ix_case_law_date", "judgment_date"),
        Index(
            "ix_case_law_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"}
        ),
    )
    
    def __repr__(self):
        return f"<CaseLaw(id={self.id}, title='{self.title[:50]}...', court='{self.court_name}')>"
