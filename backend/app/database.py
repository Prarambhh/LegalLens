"""
LegalLens Database Configuration
Async SQLAlchemy setup with pgvector support for Supabase.
"""

from typing import Optional

from sqlalchemy import text, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()

# Base class for all models (defined before engine to avoid circular imports)
Base = declarative_base()

# Engine is created lazily
_engine = None
_session_factory = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=False,  # Disable SQL echo to reduce noise
            poolclass=NullPool,
            # Supabase pooler compatibility settings
            connect_args={
                "timeout": 30,
                "command_timeout": 60,
                "statement_cache_size": 0,
                "prepared_statement_cache_size": 0,
            },
        )
    return _engine


def get_session_factory():
    """Get or create the session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db() -> AsyncSession:
    """
    Dependency injection for FastAPI routes.
    Yields a database session and ensures cleanup.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> bool:
    """
    Initialize database tables.
    Run this once to create all tables.
    """
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            # Enable pgvector extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        print("Database initialized")
        return True
    except Exception as e:
        print(f"Database initialization failed: {e}")
        print("   The API will start but database features won't work.")
        return False


async def close_db():
    """Close database connections."""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
