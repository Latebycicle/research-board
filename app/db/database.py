"""
Database connection and session management for Research Board API.

This module sets up SQLAlchemy engine, session factory, and base model class
for the Research Board application.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.engine import Engine
from typing import Generator
import logging

from app.config import settings, get_database_url

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine: Engine = create_engine(
    get_database_url(),
    echo=settings.DATABASE_ECHO,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    pool_pre_ping=True
)

# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
