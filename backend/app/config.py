"""
LegalLens Backend Configuration
Loads environment variables and provides typed settings.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str

    from pydantic import field_validator
    
    @field_validator("database_url")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str]) -> str:
        if v:
             # Force Session Mode (5432) instead of Transaction Mode (6543)
             # to avoid "prepared statement already exists" errors with asyncpg
             if ":6543" in v:
                 v = v.replace(":6543", ":5432")
             
             if v.startswith("postgresql://"):
                 v = v.replace("postgresql://", "postgresql+asyncpg://")
        
        # Force disable prepared statements for Supabase transaction mode
        if "statement_cache_size" not in v:
            if "?" in v:
                v += "&statement_cache_size=0"
            else:
                v += "?statement_cache_size=0"
        return v
    
    # AI/LLM
    google_api_key: str
    groq_api_key: Optional[str] = None
    huggingface_token: Optional[str] = None
    
    # Embedding Configuration
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dimension: int = 384
    
    # Application
    debug: bool = False
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
