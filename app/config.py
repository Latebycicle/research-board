"""
Configuration settings for the Research Board API.

This module contains all configuration variables and environment-based
settings for the FastAPI application.
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or defaults.
    """
    
    # API Configuration
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./data/app.db"
    DATABASE_ECHO: bool = False  # Set to True for SQL query logging
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Vue.js dev server
        "http://127.0.0.1:3000",
        "http://localhost:8080",  # Alternative Vue.js port
        "http://127.0.0.1:8080",
        "chrome-extension://*",    # Chrome extension
        "moz-extension://*",       # Firefox extension (future support)
    ]
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application Settings
    MAX_PAGE_CONTENT_LENGTH: int = 50000  # Maximum content length to store
    MAX_CONTENT_LEN: int = 500000  # Maximum content_html length before truncation
                                   # Long HTML content will be truncated to avoid database issues
    MAX_HIGHLIGHTS_PER_PAGE: int = 100    # Maximum highlights per page
    ENABLE_SEMANTIC_SEARCH: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        """Pydantic configuration for environment variable loading."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create global settings instance
settings = Settings()


def get_database_url() -> str:
    """
    Get the properly formatted database URL.
    
    Returns:
        str: SQLite database URL with absolute path
    """
    if settings.DATABASE_URL.startswith("sqlite:///./"):
        # Convert relative path to absolute for better reliability
        db_path = settings.DATABASE_URL.replace("sqlite:///./", "")
        abs_path = os.path.abspath(db_path)
        return f"sqlite:///{abs_path}"
    return settings.DATABASE_URL


def is_development() -> bool:
    """
    Check if the application is running in development mode.
    
    Returns:
        bool: True if in development mode
    """
    return settings.DEBUG


def is_production() -> bool:
    """
    Check if the application is running in production mode.
    
    Returns:
        bool: True if in production mode
    """
    return not settings.DEBUG
