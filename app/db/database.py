"""
Database connection and session management for Research Board API.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.engine import Engine
from typing import Generator
import logging
import os

from app.config import settings

logger = logging.getLogger(__name__)

# --- Database Setup ---
engine: Engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# --- Combined Connection Setup ---
@event.listens_for(engine, "connect")
def on_connect(dbapi_connection, connection_record):
    """
    Master function to configure each new SQLite connection.
    It enables foreign keys and loads the necessary VSS extensions.
    """
    logger.info("Setting up new SQLite connection...")
    
    # 1. Enable Foreign Key support
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
    logger.info("Foreign key support enabled.")
    
    # 2. Load vector search extensions
    try:
        dbapi_connection.enable_load_extension(True)
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Define paths to the extension files in the project root
        vector_path = os.path.join(project_root, 'vector0.dylib')
        vss_path = os.path.join(project_root, 'vss0.dylib')

        # Load vector0, which is a dependency for vss0
        if os.path.exists(vector_path):
            dbapi_connection.load_extension(vector_path)
            logger.info(f"Loaded SQLite extension: {vector_path}")
        else:
            logger.warning(f"vector0.dylib not found at {vector_path}")

        # Load vss0
        if os.path.exists(vss_path):
            dbapi_connection.load_extension(vss_path)
            logger.info(f"Loaded SQLite extension: {vss_path}")
        else:
            logger.warning(f"vss0.dylib not found at {vss_path}")
            
    except Exception as e:
        logger.error(f"Failed to load sqlite-vss extensions: {e}", exc_info=True)

# --- Session and Model Base Setup ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Session Dependency ---
def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()