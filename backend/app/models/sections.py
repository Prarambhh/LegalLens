"""
Sections Model
Represents individual sections within legal acts, with vector embeddings for RAG.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.database import Base
from app.config import get_settings

settings = get_settings()

# Embedding dimension: 384 for sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIM = settings.embedding_dimension


class Section(Base):
    """
    Individual section of a legal act.
    
    Contains the full text content and vector embedding for semantic search.
    Each section is a complete, self-contained legal provision.
    """
    __tablename__ = "sections"
    
    id = Column(Integer, primary_key=True, index=True)
    act_id = Column(Integer, ForeignKey("acts.id", ondelete="CASCADE"), nullable=False)
    
    # Section identification
    chapter_number = Column(String(20), nullable=True)  # e.g., "II", "2", "III-A"
    chapter_title = Column(String(500), nullable=True)  # e.g., "Of Punishments"
    section_number = Column(String(20), nullable=False)  # e.g., "302", "420", "1A"
    title = Column(String(500), nullable=True)  # Section title/heading
    
    # Content
    content = Column(Text, nullable=False)  # Full section text
    
    # Vector embedding for semantic search (384 dimensions for MiniLM-L6)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=True)
    
    # Metadata
    keywords = Column(String(500), nullable=True)  # Comma-separated keywords
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    act = relationship("Act", back_populates="sections")
    
    # Mappings (this section as old law)
    mappings_as_old = relationship(
        "Mapping",
        foreign_keys="Mapping.old_section_id",
        back_populates="old_section",
        cascade="all, delete-orphan"
    )
    
    # Mappings (this section as new law)
    mappings_as_new = relationship(
        "Mapping",
        foreign_keys="Mapping.new_section_id",
        back_populates="new_section",
        cascade="all, delete-orphan"
    )
    
    # Indexes for fast lookup and vector search
    __table_args__ = (
        Index("ix_sections_act_section", "act_id", "section_number"),
        Index(
            "ix_sections_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"}
        ),
    )
    
    def __repr__(self):
        return f"<Section(id={self.id}, section={self.section_number}, title='{self.title}')>"
