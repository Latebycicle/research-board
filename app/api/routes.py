"""
API routes for the Research Board application.

This module defines the main API router and route handlers for handling
web page data, highlights, history, and search functionality.
"""

from typing import List, Optional, Any, Dict, Union
from fastapi import APIRouter, Request, status, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging

from app.db.database import get_db
from app.content_processor import ContentProcessor
from app.models.models import now
from app.schemas import (
    PageCreate, PageDetailRead, PageBasicRead, PageUpdate, 
    PageAccessUpdate, EmbeddingCreate, EmbeddingCreateRequest, TimeSpentBase, 
    SemanticSearchQuery, SearchResult, MessageResponse, 
    HistoryCreate, HistoryRead, PageType, ImageCreate, HistoryAction
)
import app.crud as crud

# Set up logger
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter()


@router.get("/health", tags=["Health"])
async def api_health():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "service": "research-board-api"
    }


# Pages endpoints
@router.post(
    "/pages", 
    response_model=PageDetailRead, 
    status_code=status.HTTP_201_CREATED,
    tags=["Pages"]
)
def create_page(
    page_data: PageCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new page with optional related data.
    
    Supports creation of a page with:
    - Basic metadata (title, author, etc.)
    - Related images
    - PDF metadata (if page_type is 'pdf')
    - Embeddings
    """
    # Always create a new page - duplicate URLs are now allowed
    # This enables capturing page changes over time
    
    return crud.create_page(db=db, page_data=page_data)


@router.get(
    "/pages/{page_id}", 
    response_model=PageDetailRead,
    tags=["Pages"]
)
def read_page(
    page_id: int, 
    include_embedding: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get a page by ID with all related data.
    
    Query Parameters:
    - include_embedding: If true, includes raw embedding vectors
    """
    db_page = crud.get_page(db, page_id, include_embedding=include_embedding)
    if db_page is None:
        raise HTTPException(status_code=404, detail=f"Page with ID {page_id} not found")
    return db_page


@router.patch(
    "/pages/{page_id}/access", 
    response_model=PageDetailRead,
    tags=["Pages"]
)
def update_page_access(
    page_id: int,
    update_data: PageAccessUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a page's accessed_at timestamp and optionally add to time spent.
    """
    db_page = crud.update_page_access(
        db, 
        page_id, 
        time_spent_seconds=update_data.time_spent_seconds
    )
    if db_page is None:
        raise HTTPException(status_code=404, detail=f"Page with ID {page_id} not found")
    return db_page


@router.post(
    "/pages/{page_id}/embedding",
    response_model=PageDetailRead,
    tags=["Embeddings"]
)
def add_page_embedding(
    page_id: int, 
    embedding_data: Union[EmbeddingCreate, EmbeddingCreateRequest],
    db: Session = Depends(get_db)
):
    """
    Add a new embedding vector to an existing page.
    
    Accepts embedding data in two formats:
    - EmbeddingCreate with 'embedding' field for backwards compatibility
    - EmbeddingCreateRequest with 'vector' field for new clients
    """
    # Check if page exists
    db_page = db.query(crud.Page).filter(crud.Page.id == page_id).first()
    if db_page is None:
        raise HTTPException(status_code=404, detail=f"Page with ID {page_id} not found")
    
    # Add the embedding
    crud.add_embedding(db, page_id, embedding_data)
    
    # Return the updated page (with embedding metadata)
    return crud.get_page(db, page_id)


@router.post(
    "/pages/{page_id}/time-spent",
    response_model=MessageResponse,
    tags=["Pages"]
)
def add_page_time_spent(
    page_id: int, 
    time_data: TimeSpentBase,
    db: Session = Depends(get_db)
):
    """
    Add time spent to a page.
    """
    result = crud.add_time_spent_increment(db, page_id, time_data.seconds)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Page with ID {page_id} not found")
    
    return MessageResponse(message=f"Added {time_data.seconds} seconds to page {page_id}")


@router.get(
    "/pages", 
    response_model=List[PageBasicRead],
    tags=["Pages"]
)
def list_pages(
    page_type: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(20, gt=0, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List pages with optional filtering and pagination.
    
    Query Parameters:
    - page_type: Filter by page type ('web', 'pdf', or 'remember')
    - q: Search query text (searches title and URL)
    - limit: Maximum number of results (default: 20, max: 100)
    - offset: Number of results to skip (for pagination)
    """
    return crud.get_pages(db, page_type=page_type, query_text=q, limit=limit, offset=offset)


@router.get(
    "/pages/by-url",
    response_model=Optional[PageDetailRead],
    tags=["Pages"]
)
def get_page_by_url(
    url: str = Query(..., description="URL to search for"),
    include_remember: bool = Query(False, description="Include remember-type pages in search"),
    db: Session = Depends(get_db)
):
    """
    Find the most recent page matching the provided URL.
    
    By default, excludes 'remember' type pages unless specifically requested.
    Returns null if no matching page is found.
    
    Query Parameters:
    - url: The URL to search for
    - include_remember: Whether to include 'remember' type pages (default: false)
    """
    page = crud.get_page_by_url(
        db=db, 
        url=url,
        include_remember=include_remember
    )
    return page


@router.get(
    "/history", 
    response_model=List[HistoryRead],
    tags=["History"]
)
def list_history(
    page_id: Optional[int] = None,
    limit: int = Query(50, gt=0, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List history entries, optionally filtered by page.
    
    Query Parameters:
    - page_id: Filter by page ID
    - limit: Maximum number of results (default: 50, max: 100)
    - offset: Number of results to skip (for pagination)
    """
    return crud.get_history(db, page_id=page_id, limit=limit, offset=offset)


@router.post(
    "/history",
    response_model=HistoryRead,
    status_code=status.HTTP_201_CREATED,
    tags=["History"]
)
def create_history_entry(
    history_data: HistoryCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new history entry for a page.
    
    Records a user interaction event such as PAGE_VIEW, PAGE_CREATED, etc.
    """
    # Check if the page exists
    page = db.query(crud.Page).filter(crud.Page.id == history_data.page_id).first()
    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page with ID {history_data.page_id} not found"
        )
    
    # Create history entry
    return crud.create_history(db=db, history_data=history_data)


@router.post(
    "/search/semantic", 
    response_model=List[SearchResult],
    tags=["Search"]
)
def semantic_search(
    query: SemanticSearchQuery,
    db: Session = Depends(get_db)
):
    """
    Perform semantic similarity search using a vector.
    
    Currently uses a basic cosine similarity implementation.
    TODO: Replace with sqlite-vss for better performance.
    """
    # Perform the search
    results = crud.semantic_search(
        db, 
        query.vector, 
        model_name=query.model_name, 
        top_k=query.top_k
    )
    
    # Format the results
    search_results = []
    for page_id, score in results:
        # Get basic page info
        page = db.query(crud.Page).filter(crud.Page.id == page_id).first()
        search_results.append(
            SearchResult(
                page_id=page_id,
                score=score,
                page=page if page else None
            )
        )
    
    return search_results


@router.post("/collect", tags=["Collect"])
async def collect_content(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint to process and store incoming raw HTML content from extension.
    
    Expects JSON: {
        "html": "...", 
        "url": "...", 
        "title": "...", 
        "meta": {...}, 
        "images": [...], 
        "text": "...", 
        "accessedAt": "..."
    }
    
    Returns processed text, minimal HTML, and metadata.
    """
    try:
        data = await request.json()
        logger.info(f"[ResearchBoard] Received /collect payload: {data}")
        
        html = data.get("html")
        url = data.get("url")
        title = data.get("title")
        meta = data.get("meta", {})
        images_data = data.get("images", [])
        raw_text = data.get("text")
        accessed_at = data.get("accessedAt")
        
        if not html or not url:
            logger.error(f"[ResearchBoard] Missing html or url in payload: {data}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing html or url")
        
        # Process HTML content
        result = ContentProcessor.process(html, url)
        logger.info(f"[ResearchBoard] Processed content for: {url}")
        
        if result.get("error"):
            logger.error(f"[ResearchBoard] ContentProcessor error: {result['error']}")
            return JSONResponse(status_code=400, content={"error": result["error"]})
        
        # Prepare page data
        page_data = PageCreate(
            url=url,
            title=result["title"] or title,
            author=result.get("author"),
            publish_date=result.get("publish_date"),
            content_html=result["html"],
            page_type=PageType.WEB,
            images=[
                ImageCreate(
                    image_url=img.get("src", ""),
                    alt_text=img.get("alt", "")
                )
                for img in images_data if img.get("src")
            ]
        )
        
        # Store in database
        try:
            page = crud.create_page(db=db, page_data=page_data)
            logger.info(f"[ResearchBoard] Stored page id {page.id} for url {url}")
            
            return {
                "success": True,
                "page_id": page.id,
                "title": result["title"] or title,
                "author": result.get("author"),
                "publish_date": result.get("publish_date"),
                "content_hash": result.get("content_hash"),
                "text": result.get("text"),
                "html": result.get("html"),
                "meta": meta,
                "images": images_data,
                "accessed_at": accessed_at
            }
        except Exception as db_error:
            logger.error(f"[ResearchBoard] Database error: {db_error}")
            return JSONResponse(
                status_code=500, 
                content={"error": f"Database error: {str(db_error)}"}
            )
            
    except Exception as e:
        logger.error(f"[ResearchBoard] Exception in /collect: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
