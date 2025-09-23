"""
FastAPI application entry point for the Research Board backend.

This module sets up the main FastAPI application with CORS middleware,
routers, and essential endpoints for the research assistant.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.db.database import engine, Base
from sqlalchemy import text

from app.api.routes import router as api_router

import app.crud as crud
import os
from app.vector_store import faiss_index


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    Creates database tables on startup.
    """
    # Startup
    logger.info("Starting up Research Board backend...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

    # Create/load FAISS index
    from sqlalchemy.orm import Session
    session = Session(bind=engine)
    if os.path.exists(faiss_index.index_path):
        logger.info(f"Loading FAISS index from {faiss_index.index_path}")
        faiss_index.load_index()
    else:
        logger.info("Building FAISS index from database embeddings...")
        all_embeddings = crud.get_all_embeddings(session)
        if all_embeddings:
            faiss_index.index.reset()
            for page_id, vector in all_embeddings:
                faiss_index.add(page_id, vector)
            faiss_index.save_index()
            logger.info("FAISS index built and saved.")
        else:
            logger.info("No embeddings found in database; FAISS index is empty.")
    session.close()

    yield

    # Shutdown
    logger.info("Shutting down Research Board backend...")


# Create FastAPI application
app = FastAPI(
    title="Research Board API",
    description="A multimodal research assistant backend for collecting and organizing browsing activity",
    version=settings.API_VERSION,
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    """
    Root endpoint returning a welcome message.
    
    Returns:
        dict: Welcome message with API information
    """
    return {
        "message": "Welcome to Research Board API",
        "description": "A multimodal desktop research assistant",
        "version": settings.API_VERSION,
        "docs": f"{settings.API_PREFIX}/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring application status.
    
    Returns:
        dict: Application health status
    """
    try:
        # You could add database connectivity check here
        return {
            "status": "healthy",
            "service": "research-board-api",
            "version": settings.API_VERSION
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "research-board-api",
                "error": str(e)
            }
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
