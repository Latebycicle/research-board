"""
Database connection and session management for Research Board API.

This module sets up SQLAlchemy engine, session factory, and base model class
for the Research Board application.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
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
    
    This function creates a database session, yields it for use in route handlers,
    and ensures it's properly closed after use.
    
    Yields:
        Session: SQLAlchemy database session
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


def create_tables() -> None:
    """
    Create all database tables based on defined models.
    
    This function should be called during application startup to ensure
    all required tables exist in the database.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise


def drop_tables() -> None:
    """
    Drop all database tables.
    
    Warning: This will delete all data in the database.
    Use only for development or testing purposes.
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {str(e)}")
        raise


def get_engine() -> Engine:
    """
    Get the SQLAlchemy engine instance.
    
    Returns:
        Engine: SQLAlchemy engine
    """
    return engine


def test_connection() -> bool:
    """
    Test database connection.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False
