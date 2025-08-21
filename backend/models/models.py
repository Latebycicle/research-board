"""
Database models for the Research Board application.

This module defines SQLAlchemy models for storing web pages, highlights,
browsing history, and related data for the research assistant.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List

from app.db.database import Base


class Page(Base):
    """
    Model representing a web page or PDF document.
    
    Stores metadata and content for pages visited by the user,
    including URLs, titles, content, and processing status.
    """
    
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), nullable=False, index=True)
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    content_type = Column(String(50), default="text/html")  # html, pdf, etc.
    word_count = Column(Integer, default=0)
    
    # Processing flags
    is_processed = Column(Boolean, default=False)
    is_summarized = Column(Boolean, default=False)
    is_indexed = Column(Boolean, default=False)  # For semantic search
    
    # Metadata
    domain = Column(String(255), nullable=True, index=True)
    favicon_url = Column(String(1024), nullable=True)
    description = Column(Text, nullable=True)
    keywords = Column(String(1000), nullable=True)
    
    # AI-generated content
    summary = Column(Text, nullable=True)
    key_points = Column(Text, nullable=True)  # JSON array of key points
    sentiment_score = Column(Float, nullable=True)  # -1 to 1
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_visited = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    highlights = relationship("Highlight", back_populates="page", cascade="all, delete-orphan")
    history_entries = relationship("History", back_populates="page", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Page(id={self.id}, url='{self.url[:50]}...', title='{self.title}')>"


class Highlight(Base):
    """
    Model representing user highlights and "Remember This" selections.
    
    Stores text/content that users have explicitly marked as important,
    along with context and metadata.
    """
    
    __tablename__ = "highlights"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False, index=True)
    
    # Highlight content
    selected_text = Column(Text, nullable=False)
    surrounding_context = Column(Text, nullable=True)  # Text around the selection
    highlight_type = Column(String(50), default="text")  # text, image, quote, etc.
    
    # Position information
    xpath = Column(String(1000), nullable=True)  # XPath to the element
    start_offset = Column(Integer, nullable=True)
    end_offset = Column(Integer, nullable=True)
    
    # User annotations
    user_note = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    importance_score = Column(Integer, default=5)  # 1-10 scale
    
    # AI analysis
    summary = Column(Text, nullable=True)
    key_concepts = Column(Text, nullable=True)  # JSON array
    related_topics = Column(Text, nullable=True)  # JSON array
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    page = relationship("Page", back_populates="highlights")
    
    def __repr__(self) -> str:
        preview = self.selected_text[:50] + "..." if len(self.selected_text) > 50 else self.selected_text
        return f"<Highlight(id={self.id}, page_id={self.page_id}, text='{preview}')>"


class History(Base):
    """
    Model representing browsing history entries.
    
    Tracks when and how users interact with pages, including visit duration,
    scroll behavior, and interaction patterns.
    """
    
    __tablename__ = "history"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False, index=True)
    
    # Visit information
    visit_start = Column(DateTime, default=func.now(), nullable=False)
    visit_end = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Interaction data
    scroll_depth_percent = Column(Float, nullable=True)  # 0-100
    clicks_count = Column(Integer, default=0)
    time_active_seconds = Column(Integer, nullable=True)  # Time actually engaging
    
    # Navigation context
    referrer_url = Column(String(2048), nullable=True)
    entry_point = Column(String(50), nullable=True)  # search, bookmark, direct, etc.
    exit_action = Column(String(50), nullable=True)   # close, navigate, etc.
    
    # Device/browser information
    user_agent = Column(String(500), nullable=True)
    screen_resolution = Column(String(20), nullable=True)  # "1920x1080"
    viewport_size = Column(String(20), nullable=True)      # "1200x800"
    
    # Session information
    session_id = Column(String(100), nullable=True, index=True)
    tab_id = Column(String(50), nullable=True)
    window_id = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    page = relationship("Page", back_populates="history_entries")
    
    def __repr__(self) -> str:
        return f"<History(id={self.id}, page_id={self.page_id}, visit_start='{self.visit_start}')>"


class SearchQuery(Base):
    """
    Model for storing user search queries and results.
    
    Tracks semantic searches performed by users to improve recommendations
    and understand research patterns.
    """
    
    __tablename__ = "search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Query information
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50), default="semantic")  # semantic, keyword, etc.
    results_count = Column(Integer, default=0)
    
    # Results metadata
    top_result_ids = Column(Text, nullable=True)  # JSON array of page/highlight IDs
    avg_relevance_score = Column(Float, nullable=True)
    
    # Context
    search_context = Column(String(100), nullable=True)  # research_topic, quick_lookup, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<SearchQuery(id={self.id}, query='{self.query_text[:50]}...', results={self.results_count})>"


class Tag(Base):
    """
    Model for organizing content with tags.
    
    Allows users to categorize pages and highlights with custom tags
    for better organization and retrieval.
    """
    
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), default="#3498db")  # Hex color code
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name='{self.name}', usage_count={self.usage_count})>"
