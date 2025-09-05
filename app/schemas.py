"""
Pydantic schemas for API request and response validation.

This module defines the data models used for API input/output validation
using Pydantic's data validation system.
"""

from pydantic import BaseModel, Field, HttpUrl, constr, validator
from typing import List, Optional, Union, Dict, Any
import datetime
from enum import Enum


class PageType(str, Enum):
    """Valid page types."""
    WEB = "web"
    PDF = "pdf"
    REMEMBER = "remember"  # New type for remember pages


class HistoryAction(str, Enum):
    """Valid history action types."""
    OPENED = "opened"
    CLOSED = "closed"
    HIGHLIGHTED = "highlighted"
    ACCESSED = "accessed"  # New action type


# Base schemas
class ImageBase(BaseModel):
    """Base schema for image data."""
    image_url: str
    alt_text: Optional[str] = None


class PDFBase(BaseModel):
    """Base schema for PDF metadata."""
    file_path: str
    num_pages: Optional[int] = None
    size_bytes: Optional[int] = None


class EmbeddingBase(BaseModel):
    """Base schema for embedding vectors."""
    model_name: str
    embedding: List[float]  # Will be renamed to vector in API requests
    
    model_config = {"protected_namespaces": ()}


class EmbeddingCreateRequest(BaseModel):
    """Schema for embedding in API requests."""
    model_name: str
    vector: List[float]  # Using 'vector' instead of 'embedding' in API
    
    model_config = {"protected_namespaces": ()}


class TimeSpentBase(BaseModel):
    """Base schema for page time tracking."""
    seconds: int = Field(..., gt=0)


class HistoryBase(BaseModel):
    """Base schema for history entries."""
    action: HistoryAction
    session_id: Optional[str] = None


class UserBase(BaseModel):
    """Base schema for user data."""
    name: str
    email: Optional[str] = None


# Create schemas
class ImageCreate(ImageBase):
    """Schema for creating a new image record."""
    pass


class PDFCreate(PDFBase):
    """Schema for creating a new PDF record."""
    pass


class EmbeddingCreate(EmbeddingBase):
    """Schema for creating a new embedding record."""
    pass


class PageCreate(BaseModel):
    """Schema for creating a new page record."""
    url: str
    title: Optional[str] = None
    author: Optional[str] = None
    publish_date: Optional[datetime.datetime] = None
    content_html: str
    highlight: Optional[str] = None
    page_type: PageType
    images: Optional[List[ImageCreate]] = None
    pdf: Optional[PDFCreate] = None  # Required only when page_type='pdf'
    embeddings: Optional[List[EmbeddingCreateRequest]] = None  # Optional embeddings with vector field


class HistoryCreate(HistoryBase):
    """Schema for creating a new history entry."""
    page_id: int


class UserCreate(UserBase):
    """Schema for creating a new user."""
    pass


# Read schemas
class ImageRead(ImageBase):
    """Schema for reading image data."""
    id: int
    page_id: int
    created_at: datetime.datetime
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PDFRead(PDFBase):
    """Schema for reading PDF data."""
    id: int
    page_id: int
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class EmbeddingMetadataRead(BaseModel):
    """Schema for reading embedding metadata (without vector)."""
    id: int
    model_name: str
    created_at: datetime.datetime
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class EmbeddingFullRead(EmbeddingMetadataRead):
    """Schema for reading complete embedding data (with vector)."""
    embedding: List[float]


class TimeSpentRead(BaseModel):
    """Schema for reading page time data."""
    total_seconds: int
    last_updated: datetime.datetime
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class HistoryRead(HistoryBase):
    """Schema for reading history entries."""
    id: int
    page_id: int
    accessed_at: datetime.datetime
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PageBasicRead(BaseModel):
    """Schema for basic page information (list view)."""
    id: int
    url: str
    title: Optional[str] = None
    page_type: str
    created_at: datetime.datetime
    accessed_at: Optional[datetime.datetime] = None
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PageDetailRead(PageBasicRead):
    """Schema for detailed page information (detail view)."""
    author: Optional[str] = None
    publish_date: Optional[datetime.datetime] = None
    content_html: Optional[str] = None
    highlight: Optional[str] = None
    images: List[ImageRead] = []
    pdf: Optional[PDFRead] = None
    time_spent: Optional[TimeSpentRead] = None
    embeddings: List[EmbeddingMetadataRead] = []
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PageWithEmbeddingRead(PageDetailRead):
    """Schema for page with full embedding data (for search)."""
    embeddings: List[EmbeddingFullRead] = []


# Update schemas
class PageUpdate(BaseModel):
    """Schema for updating page data."""
    title: Optional[str] = None
    author: Optional[str] = None
    highlight: Optional[str] = None
    accessed_at: Optional[datetime.datetime] = None  # Allow manual timestamp updates


class HistoryCreateRequest(BaseModel):
    """Schema for creating a history entry via API."""
    page_id: int
    action: str
    session_id: Optional[str] = None


class PageAccessUpdate(BaseModel):
    """Schema for updating page access information."""
    time_spent_seconds: Optional[int] = Field(None, gt=0)


# Search schemas
class SemanticSearchQuery(BaseModel):
    """Schema for semantic search requests."""
    vector: List[float]
    top_k: int = Field(default=5, gt=0)
    model_name: Optional[str] = None


class SearchResult(BaseModel):
    """Schema for search results."""
    page_id: int
    score: float
    page: Optional[PageBasicRead] = None


class ListPagesParams(BaseModel):
    """Query parameters for listing pages."""
    page_type: Optional[PageType] = None
    q: Optional[str] = None
    limit: int = Field(default=20, gt=0, le=100)
    offset: int = Field(default=0, ge=0)


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str