"""
Database models for the Research Board application.

This module defines SQLAlchemy models for storing web pages, highlights,
browsing history, and related data for the research assistant.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, CheckConstraint, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import datetime
from typing import Optional, List

from app.db.database import Base

def now() -> datetime.datetime:
    """Return current UTC timestamp for consistent datetime handling."""
    return datetime.datetime.utcnow()

class User(Base):
    """User model for authentication and personalization."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(255), unique=True, nullable=True)

class Page(Base):
    """Primary model for storing web and PDF pages."""
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True)
    url = Column(Text, unique=True, nullable=False, index=True)
    title = Column(Text, nullable=True)
    author = Column(Text, nullable=True)
    publish_date = Column(DateTime, nullable=True)
    content_html = Column(Text, nullable=True)  # Cleaned HTML or extracted text for PDFs
    text = Column(Text, nullable=True)  # Cleaned plain text from content processor
    highlight = Column(Text, nullable=True)  # Single highlight, TODO: create separate table for multiple highlights
    page_type = Column(String(10), nullable=False)  # 'web' or 'pdf'
    created_at = Column(DateTime, default=now, nullable=False)
    accessed_at = Column(DateTime, nullable=True)
    
    # Relationships
    images = relationship("Image", back_populates="page", cascade="all, delete-orphan")
    pdf = relationship("PDF", back_populates="page", uselist=False, cascade="all, delete-orphan")
    embeddings = relationship("Embedding", back_populates="page", cascade="all, delete-orphan")
    time_spent = relationship("PageTimeSpent", back_populates="page", uselist=False, cascade="all, delete-orphan")
    history_entries = relationship("History", back_populates="page", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("page_type IN ('web', 'pdf')", name="valid_page_type"),
    )

class Image(Base):
    """Images associated with a page."""
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(Text, nullable=False)
    alt_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now, nullable=False)
    
    page = relationship("Page", back_populates="images")

class PDF(Base):
    """Additional metadata for PDF documents."""
    __tablename__ = "pdfs"
    
    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, unique=True)
    file_path = Column(Text, nullable=False)
    num_pages = Column(Integer, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    
    page = relationship("Page", back_populates="pdf")

class Embedding(Base):
    """Vector embeddings for semantic search."""
    __tablename__ = "embeddings"
    
    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    embedding = Column(LargeBinary, nullable=False)  # Store as float32 vector
    model_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=now, nullable=False)
    
    page = relationship("Page", back_populates="embeddings")

class PageTimeSpent(Base):
    """Track time spent on each page."""
    __tablename__ = "page_time_spent"
    
    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_seconds = Column(Integer, default=0, nullable=False)
    last_updated = Column(DateTime, default=now, nullable=False)
    
    page = relationship("Page", back_populates="time_spent")

class History(Base):
    """User interaction history with pages."""
    __tablename__ = "history"
    
    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    accessed_at = Column(DateTime, default=now, nullable=False)
    action = Column(String(20), nullable=False)  # 'opened', 'closed', 'highlighted'
    session_id = Column(String(100), nullable=True)
    
    page = relationship("Page", back_populates="history_entries")
