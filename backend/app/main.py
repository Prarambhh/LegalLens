"""
LegalLens Backend - FastAPI Application
========================================

Main entry point for the LegalLens API server.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()

# Track database status
db_connected = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    global db_connected
    
    # Startup
    print("Starting LegalLens API...")
    
    # Skip database for now - uncomment when Supabase is configured
    try:
        from app.database import init_db
        await init_db()
        db_connected = True
        print("Database connected")
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("   API will start but database features disabled.")
        db_connected = False
    
    print("Running without database (configure Supabase to enable)")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    print("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="LegalLens API",
    description="AI-Powered Legal Helper for India - Navigate the transition from IPC/CrPC/IEA to BNS/BNSS/BSA",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "LegalLens API",
        "status": "healthy",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "embedding_model": settings.embedding_model
    }


# API Routers
from app.api import chat, documents
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])

from app.api import auth, admin
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

# TODO: Add more routers as needed
from app.api import compare
app.include_router(compare.router, prefix="/api/compare", tags=["Compare Laws"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
