"""
CRUD operations for database entities.

This module provides helper functions for Create, Read, Update, Delete
operations on database models, abstracting SQL operations.
"""

from sqlalchemy.orm import Session, joinedload, contains_eager
from sqlalchemy import func, select, desc, text
from typing import List, Optional, Tuple, Dict, Any, Union
import datetime
import struct
import numpy as np
from app.models.models import (
    Page, Image, PDF, Embedding, PageTimeSpent, 
    History, User, now
)
from app.schemas import (
    PageCreate, ImageCreate, PDFCreate, EmbeddingCreate, EmbeddingCreateRequest,
    HistoryCreate, PageType, HistoryAction
)
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Helper functions for vector conversions
def float_list_to_bytes(vector: List[float]) -> bytes:
    """Convert a list of float values to a binary blob of float32."""
    return np.array(vector, dtype=np.float32).tobytes()

def bytes_to_float_list(binary_data: bytes) -> List[float]:
    """Convert a binary blob of float32 back to a list of floats."""
    float_array = np.frombuffer(binary_data, dtype=np.float32)
    # Truncate to 8 decimal places for readability and to reduce payload size
    return [float(round(x, 8)) for x in float_array]

# Page CRUD operations
def create_page(db: Session, page_data: PageCreate) -> Page:
    """
    Create a new page record with optional related data (images, PDF, embeddings).
    Always creates a NEW page record (no upsert/merge based on URL).
    
    Args:
        db: Database session
        page_data: Page data including optional nested resources
        
    Returns:
        Created Page instance with relationships populated
    """
    # Check if content_html exceeds max length and truncate if needed
    content_html = page_data.content_html
    if content_html and len(content_html) > settings.MAX_CONTENT_LEN:
        logger.warning(
            f"Content HTML for URL {page_data.url} exceeds MAX_CONTENT_LEN "
            f"({len(content_html)} > {settings.MAX_CONTENT_LEN}). Truncating."
        )
        content_html = content_html[:settings.MAX_CONTENT_LEN]
    
    # Create the base page object
    db_page = Page(
        url=page_data.url,
        title=page_data.title,
        author=page_data.author,
        publish_date=page_data.publish_date,
        content_html=content_html,
        highlight=page_data.highlight,
        page_type=page_data.page_type,
        created_at=now(),
        accessed_at=now()
    )
    db.add(db_page)
    db.flush()  # Get the ID without committing
    
    # Create the time spent record
    db_time_spent = PageTimeSpent(
        page_id=db_page.id,
        total_seconds=0,
        last_updated=now()
    )
    db.add(db_time_spent)
    
    # Create related images if provided
    if page_data.images:
        add_images(db, db_page.id, page_data.images)
    
    # Create PDF record if provided
    if page_data.pdf and page_data.page_type == PageType.PDF:
        # For PDF type, make sure we have at least the file_path
        db_pdf = PDF(
            page_id=db_page.id,
            file_path=page_data.pdf.file_path,
            # Default to 1 page and 0 bytes if not provided
            num_pages=page_data.pdf.num_pages or 1,
            size_bytes=page_data.pdf.size_bytes or 0
        )
        db.add(db_pdf)
    
    # Create embeddings if provided
    if page_data.embeddings:
        for embedding_request in page_data.embeddings:
            # Convert from EmbeddingCreateRequest to EmbeddingCreate
            embedding_data = EmbeddingCreate(
                model_name=embedding_request.model_name,
                embedding=embedding_request.vector
            )
            add_embedding(db, db_page.id, embedding_data)
    
    # Log the page creation in history
    log_history(db, db_page.id, HistoryAction.OPENED)
    
    db.commit()
    db.refresh(db_page)
    return db_page

def get_page(db: Session, page_id: int, include_embedding: bool = False) -> Optional[Page]:
    """
    Get a page by ID with all related data.
    
    Args:
        db: Database session
        page_id: ID of the page to retrieve
        include_embedding: Whether to include raw embedding vectors
        
    Returns:
        Page instance with relationships loaded, or None if not found
    """
    query = db.query(Page).filter(Page.id == page_id)
    
    # Always load these relationships
    query = query.options(
        joinedload(Page.images),
        joinedload(Page.pdf),
        joinedload(Page.time_spent)
    )
    
    # Conditionally load embeddings
    if include_embedding:
        query = query.options(joinedload(Page.embeddings))
    else:
        # Just load metadata without the actual vectors
        query = query.options(
            joinedload(Page.embeddings).load_only(
                Embedding.id, Embedding.model_name, Embedding.created_at
            )
        )
    
    return query.first()


def get_page_by_url(
    db: Session, 
    url: str, 
    include_remember: bool = False,
    include_embedding: bool = False
) -> Optional[Page]:
    """
    Get the most recent page with a specific URL.
    
    Args:
        db: Database session
        url: URL to search for
        include_remember: Whether to include 'remember' type pages
        include_embedding: Whether to include raw embedding vectors
        
    Returns:
        Most recent Page instance with the given URL, or None if not found
    """
    query = db.query(Page).filter(Page.url == url)
    
    # Exclude 'remember' pages unless explicitly requested
    if not include_remember:
        query = query.filter(Page.page_type != PageType.REMEMBER)
    
    # Always load these relationships
    query = query.options(
        joinedload(Page.images),
        joinedload(Page.pdf),
        joinedload(Page.time_spent)
    )
    
    # Conditionally load embeddings
    if include_embedding:
        query = query.options(joinedload(Page.embeddings))
    else:
        # Just load metadata without the actual vectors
        query = query.options(
            joinedload(Page.embeddings).load_only(
                Embedding.id, Embedding.model_name, Embedding.created_at
            )
        )
    
    # Order by most recent (highest ID) and return the first
    return query.order_by(Page.id.desc()).first()

def get_pages(
    db: Session, 
    page_type: Optional[str] = None, 
    query_text: Optional[str] = None,
    limit: int = 20, 
    offset: int = 0
) -> List[Page]:
    """
    List pages with optional filtering.
    
    Args:
        db: Database session
        page_type: Optional filter by page type ('web' or 'pdf')
        query_text: Optional search text to filter by title/url (LIKE query)
        limit: Maximum number of results to return
        offset: Number of results to skip
        
    Returns:
        List of Page instances
    """
    query = db.query(Page)
    
    # Apply filters if provided
    if page_type:
        query = query.filter(Page.page_type == page_type)
    
    if query_text:
        # Basic LIKE search on title and URL
        # TODO: Replace with FTS5 for better performance and search quality
        search_term = f"%{query_text}%"
        query = query.filter(
            (Page.title.ilike(search_term)) | 
            (Page.url.ilike(search_term))
        )
    
    # Order by most recently accessed
    query = query.order_by(Page.accessed_at.desc().nullslast(), Page.created_at.desc())
    
    # Apply pagination
    return query.offset(offset).limit(limit).all()

def update_page(db: Session, page_id: int, page_data: Dict[str, Any]) -> Optional[Page]:
    """
    Update a page with new data.
    
    Args:
        db: Database session
        page_id: ID of the page to update
        page_data: Dictionary of fields to update
        
    Returns:
        Updated Page instance, or None if not found
    """
    db_page = db.query(Page).filter(Page.id == page_id).first()
    if not db_page:
        return None
    
    # Update fields provided in the input data
    for key, value in page_data.items():
        if hasattr(db_page, key):
            setattr(db_page, key, value)
    
    db.commit()
    db.refresh(db_page)
    return db_page

def update_page_access(
    db: Session, 
    page_id: int, 
    time_spent_seconds: Optional[int] = None,
    log_action: bool = True
) -> Optional[Page]:
    """
    Update a page's accessed_at timestamp and optionally add to time spent.
    
    Args:
        db: Database session
        page_id: ID of the page to update
        time_spent_seconds: Optional seconds to add to the total time spent
        log_action: Whether to log this access in the history table
        
    Returns:
        Updated Page instance, or None if not found
    """
    db_page = db.query(Page).filter(Page.id == page_id).first()
    if not db_page:
        return None
    
    # Update the accessed_at timestamp
    current_time = now()
    db_page.accessed_at = current_time
    
    # Update time spent if provided
    if time_spent_seconds is not None and time_spent_seconds > 0:
        db_time_spent = db.query(PageTimeSpent).filter(PageTimeSpent.page_id == page_id).first()
        
        if db_time_spent:
            db_time_spent.total_seconds += time_spent_seconds
            db_time_spent.last_updated = current_time
        else:
            # Create time spent record if it doesn't exist
            db_time_spent = PageTimeSpent(
                page_id=page_id,
                total_seconds=time_spent_seconds,
                last_updated=current_time
            )
            db.add(db_time_spent)
    
    # Log the access in history
    if log_action:
        log_history(db, page_id, HistoryAction.ACCESSED)
    
    db.commit()
    db.refresh(db_page)
    return db_page

def add_time_spent_increment(db: Session, page_id: int, seconds: int) -> Optional[PageTimeSpent]:
    """
    Add time spent to a page.
    
    Args:
        db: Database session
        page_id: ID of the page
        seconds: Seconds to add to the total
        
    Returns:
        Updated PageTimeSpent instance, or None if page not found
    """
    # Check if page exists
    db_page = db.query(Page).filter(Page.id == page_id).first()
    if not db_page:
        return None
    
    current_time = now()
    
    # Update the page's accessed_at timestamp
    db_page.accessed_at = current_time
    
    # Get or create time spent record
    db_time_spent = db.query(PageTimeSpent).filter(PageTimeSpent.page_id == page_id).first()
    
    if db_time_spent:
        db_time_spent.total_seconds += seconds
        db_time_spent.last_updated = current_time
    else:
        db_time_spent = PageTimeSpent(
            page_id=page_id,
            total_seconds=seconds,
            last_updated=current_time
        )
        db.add(db_time_spent)
    
    db.commit()
    db.refresh(db_time_spent)
    return db_time_spent

# Image CRUD operations
def add_images(db: Session, page_id: int, images: List[ImageCreate]) -> List[Image]:
    """
    Add multiple images to a page.
    
    Args:
        db: Database session
        page_id: ID of the page to associate images with
        images: List of image data
        
    Returns:
        List of created Image instances
    """
    db_images = []
    for image_data in images:
        db_image = Image(
            page_id=page_id,
            image_url=image_data.image_url,
            alt_text=image_data.alt_text,
            created_at=now()
        )
        db.add(db_image)
        db_images.append(db_image)
    
    db.flush()
    return db_images

def get_page_with_images(db: Session, page_id: int) -> Optional[Page]:
    """
    Get a page with its images eagerly loaded.
    
    Args:
        db: Database session
        page_id: ID of the page
        
    Returns:
        Page instance with images relationship populated, or None if not found
    """
    return db.query(Page).options(
        joinedload(Page.images)
    ).filter(Page.id == page_id).first()

# Embedding CRUD operations
def add_embedding(
    db: Session, 
    page_id: int, 
    embedding_data: Union[EmbeddingCreate, EmbeddingCreateRequest]
) -> Embedding:
    """
    Add an embedding vector to a page.
    
    Args:
        db: Database session
        page_id: ID of the page
        embedding_data: Embedding data including vector and model name.
          Can be either EmbeddingCreate (with 'embedding' field) or 
          EmbeddingCreateRequest (with 'vector' field).
        
    Returns:
        Created Embedding instance
    """
    # Extract the vector from either embedding or vector field
    if hasattr(embedding_data, 'embedding'):
        vector = embedding_data.embedding
    else:
        vector = embedding_data.vector
        
    # Convert the float array to binary blob
    binary_embedding = float_list_to_bytes(vector)
    
    db_embedding = Embedding(
        page_id=page_id,
        embedding=binary_embedding,
        model_name=embedding_data.model_name,
        created_at=now()
    )
    db.add(db_embedding)
    db.flush()
    return db_embedding

def get_embedding(db: Session, embedding_id: int) -> Optional[Embedding]:
    """
    Get an embedding by ID.
    
    Args:
        db: Database session
        embedding_id: ID of the embedding
        
    Returns:
        Embedding instance or None if not found
    """
    return db.query(Embedding).filter(Embedding.id == embedding_id).first()

def get_latest_embedding_by_model(
    db: Session, 
    page_id: int, 
    model_name: str
) -> Optional[Embedding]:
    """
    Get the latest embedding for a page by model name.
    
    Args:
        db: Database session
        page_id: ID of the page
        model_name: Name of the embedding model
        
    Returns:
        Latest Embedding instance or None if not found
    """
    return db.query(Embedding).filter(
        Embedding.page_id == page_id,
        Embedding.model_name == model_name
    ).order_by(Embedding.created_at.desc()).first()

def semantic_search(
    db: Session, 
    query_vector: List[float], 
    model_name: Optional[str] = None, 
    top_k: int = 5
) -> List[Tuple[int, float]]:
    """
    Perform semantic similarity search across all embeddings.
    
    Args:
        db: Database session
        query_vector: The vector to search for
        model_name: Optional filter by model name
        top_k: Number of results to return
        
    Returns:
        List of tuples (page_id, similarity_score) sorted by similarity
    """
    # Convert query vector to numpy array
    query_np = np.array(query_vector, dtype=np.float32)
    
    # Get all embeddings, optionally filtered by model
    query = db.query(Embedding.id, Embedding.page_id, Embedding.embedding)
    if model_name:
        query = query.filter(Embedding.model_name == model_name)
    
    embeddings = query.all()
    
    # If no embeddings found, return empty list
    if not embeddings:
        return []
    
    # Calculate similarities
    results = []
    for embedding_id, page_id, binary_embedding in embeddings:
        # Convert binary blob back to numpy array
        embedding_np = np.frombuffer(binary_embedding, dtype=np.float32)
        
        # Calculate cosine similarity
        # Note: For production, replace with more efficient vector search like sqlite-vss
        norm_q = np.linalg.norm(query_np)
        norm_e = np.linalg.norm(embedding_np)
        
        # Avoid division by zero
        if norm_q == 0 or norm_e == 0:
            similarity = 0
        else:
            similarity = np.dot(query_np, embedding_np) / (norm_q * norm_e)
        
        results.append((page_id, float(similarity)))
    
    # Sort by similarity (descending) and return top_k
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]

# History CRUD operations
def log_history(
    db: Session, 
    page_id: int, 
    action: HistoryAction, 
    session_id: Optional[str] = None
) -> History:
    """
    Log a history entry for a page.
    
    Args:
        db: Database session
        page_id: ID of the page
        action: Action performed (opened, closed, highlighted)
        session_id: Optional session identifier
        
    Returns:
        Created History instance
    """
    db_history = History(
        page_id=page_id,
        accessed_at=now(),
        action=action,
        session_id=session_id
    )
    db.add(db_history)
    db.flush()
    return db_history

def create_history(db: Session, history_data: HistoryCreate) -> History:
    """
    Create a new history entry.
    
    Args:
        db: Database session
        history_data: History data including page_id and action
        
    Returns:
        Created History instance
    """
    # Create history record
    db_history = History(
        page_id=history_data.page_id,
        action=history_data.action,
        accessed_at=now(),
        session_id=history_data.session_id if hasattr(history_data, 'session_id') else None
    )
    
    db.add(db_history)
    db.flush()
    
    # Update the page's accessed_at timestamp when a page is viewed
    if history_data.action == HistoryAction.PAGE_VIEW:
        page = db.query(Page).filter(Page.id == history_data.page_id).first()
        if page:
            page.accessed_at = now()
    
    db.commit()
    return db_history


def get_history(
    db: Session, 
    page_id: Optional[int] = None, 
    limit: int = 50, 
    offset: int = 0
) -> List[History]:
    """
    Get history entries, optionally filtered by page.
    
    Args:
        db: Database session
        page_id: Optional ID of the page to filter by
        limit: Maximum number of entries to return
        offset: Number of entries to skip
        
    Returns:
        List of History instances
    """
    query = db.query(History)
    
    if page_id is not None:
        query = query.filter(History.page_id == page_id)
    
    query = query.order_by(History.accessed_at.desc())
    return query.offset(offset).limit(limit).all()

# User CRUD operations
def create_user(db: Session, name: str, email: Optional[str] = None) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session
        name: User name
        email: Optional email address
        
    Returns:
        Created User instance
    """
    db_user = User(name=name, email=email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int) -> Optional[User]:
    """
    Get a user by ID.
    
    Args:
        db: Database session
        user_id: ID of the user
        
    Returns:
        User instance or None if not found
    """
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by email.
    
    Args:
        db: Database session
        email: Email address to search for
        
    Returns:
        User instance or None if not found
    """
    return db.query(User).filter(User.email == email).first()