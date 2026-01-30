"""
Mappings Model
Maps old law sections (IPC, CrPC, IEA) to new Sanhitas (BNS, BNSS, BSA).
Enables the "Law Transition Engine" feature.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class ChangeType(str, enum.Enum):
    """Type of change from old to new law."""
    REPLACED = "Replaced"          # Direct replacement with modifications
    REPEALED = "Repealed"          # Section removed, no equivalent
    NEW = "New"                    # Completely new section, no old equivalent
    UNCHANGED = "Unchanged"        # Carried forward as-is
    MERGED = "Merged"              # Multiple old sections merged into one
    SPLIT = "Split"                # One old section split into multiple


class Mapping(Base):
    """
    Maps old law sections to new law sections.
    
    Enables bidirectional search:
    - IPC Section 302 -> BNS Section 103
    - BNS Section 103 -> IPC Section 302
    
    Includes description of what changed between versions.
    """
    __tablename__ = "mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys to sections
    old_section_id = Column(
        Integer, 
        ForeignKey("sections.id", ondelete="CASCADE"), 
        nullable=True  # Nullable for NEW sections that have no old equivalent
    )
    new_section_id = Column(
        Integer, 
        ForeignKey("sections.id", ondelete="CASCADE"), 
        nullable=True  # Nullable for REPEALED sections that have no new equivalent
    )
    
    # Change details
    change_type = Column(SQLEnum(ChangeType), nullable=False, default=ChangeType.REPLACED)
    description_of_change = Column(Text, nullable=True)  # Human-readable summary
    
    # Diff data for highlighting (stored as JSON-compatible text)
    removed_text = Column(Text, nullable=True)  # Text removed from old law (for red highlights)
    added_text = Column(Text, nullable=True)    # Text added in new law (for green highlights)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    old_section = relationship(
        "Section",
        foreign_keys=[old_section_id],
        back_populates="mappings_as_old"
    )
    new_section = relationship(
        "Section",
        foreign_keys=[new_section_id],
        back_populates="mappings_as_new"
    )
    
    def __repr__(self):
        return f"<Mapping(id={self.id}, old={self.old_section_id}, new={self.new_section_id}, type={self.change_type})>"
