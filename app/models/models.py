"""
Database models for the Research Board application.

This module defines SQLAlchemy models for storing web pages, highlights,
browsing history, and related data for the research assistant.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.db.database import Base

class Page(Base):
    __tablename__ = "pages"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), nullable=False, index=True)
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    highlights = relationship("Highlight", back_populates="page", cascade="all, delete-orphan")

class Highlight(Base):
    __tablename__ = "highlights"
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False, index=True)
    selected_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    page = relationship("Page", back_populates="highlights")

class History(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False, index=True)
    visit_start = Column(DateTime, default=func.now(), nullable=False)
    page = relationship("Page")
