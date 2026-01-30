"""
Security Utilities
"""
from datetime import datetime, timedelta
from typing import Optional, Any, Union
from jose import jwt
from passlib.context import CryptContext
from app.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

ALGORITHM = "HS256"

# Create a secret key if not set in env (for dev only - in prod this comes from env)
SECRET_KEY = settings.google_api_key if settings.google_api_key else "dev_secret_key_change_me"

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def _truncate_password(password: str) -> str:
    """Truncate password to 72 bytes for bcrypt compatibility."""
    return password.encode('utf-8')[:72].decode('utf-8', errors='ignore')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(_truncate_password(plain_password), hashed_password)
    except Exception:
        # Fallback: try without truncation for old hashes
        return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(_truncate_password(password))
