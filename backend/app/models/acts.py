"""
Acts Model
Represents legal acts/statutes like BNS 2023, IPC 1860, etc.
"""

from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class ActType(str, enum.Enum):
    """Type of legal act - Central or State level."""
    CENTRAL = "Central"
    STATE = "State"


class Act(Base):
    """
    Legal Act/Statute model.
    
    Examples:
        - Bharatiya Nyaya Sanhita, 2023 (BNS)
        - Indian Penal Code, 1860 (IPC)
        - Code of Criminal Procedure, 1973 (CrPC)
        - Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)
    """
    __tablename__ = "acts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    short_name = Column(String(50), nullable=True)  # e.g., "BNS", "IPC"
    year = Column(Integer, nullable=False)
    type = Column(SQLEnum(ActType), nullable=False, default=ActType.CENTRAL)
    description = Column(String(1000), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sections = relationship("Section", back_populates="act", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Act(id={self.id}, name='{self.name}', year={self.year})>"
