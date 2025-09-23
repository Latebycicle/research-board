"""
API routes for the Research Board application.

This module defines the main API router and route handlers for handling
web page data, highlights, history, and search functionality.
"""

from app.schemas import ChatRequest
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Request, status, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging
import httpx
from app.db.database import get_db
from app.content_processor import ContentProcessor
from app.models.models import now
from app.schemas import (
    PageCreate, PageDetailRead, PageBasicRead, PageUpdate, 
    PageAccessUpdate, EmbeddingCreate, TimeSpentBase, 
    SemanticSearchRequest, SearchResult, MessageResponse, 
    HistoryRead, PageType, ImageCreate
)
import app.crud as crud



router = APIRouter()

# Set up logger
# Set up logger
logger = logging.getLogger(__name__)

# Ollama embedding helper
async def get_embedding(text: str) -> list[float]:
    """Call Ollama API to generate embedding for the given text."""
    logger.info("Generating embedding...")
    url = "http://127.0.0.1:11434/api/embeddings"
    payload = {"model": "embeddinggemma:latest", "prompt": text}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=60.0)
        response.raise_for_status()
        data = response.json()
        embedding = data.get("embedding", [])
        logger.info(f"Embedding received. First 5 values: {embedding[:5]}")
        return embedding

# Create API router


# --- RAG Chat Endpoint ---
@router.post("/chat", tags=["Chat"])
async def rag_chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    RAG chat endpoint: retrieves relevant context and sends a prompt to Ollama for completion.
    """
    # 1. Get embedding for the query
    embedding = await get_embedding(request.query)
    if not embedding or len(embedding) != 768:
        raise HTTPException(status_code=500, detail="Failed to generate embedding for query.")

    # 2. Retrieve top 3-4 relevant pages
    results = crud.semantic_search(db, embedding, top_k=4)
    page_ids = [page_id for page_id, _ in results]
    pages = crud.get_pages_by_ids(db, page_ids)

    # 3. Build context from page texts
    context_chunks = []
    sources = []
    for page in pages:
        if page.text:
            context_chunks.append(f"[Source: {page.title}]\n{page.text.strip()}\n")
            sources.append({"id": page.id, "title": page.title, "url": page.url})
    context = "\n---\n".join(context_chunks)

    # 4. Construct prompt for Ollama
    prompt = (
        "You are a research assistant. Use the following context from the user's reading history to answer the question.\n"
        f"Context:\n{context}\n"
        f"\nQuestion: {request.query}\n"
        "\nIf you use information from a source, cite it by title in your answer."
    )

    # 5. Call Ollama's chat completion endpoint
    ollama_url = "http://127.0.0.1:11434/api/chat"
    payload = {"model": "gpt-oss:20b", "messages": [{"role": "user", "content": prompt}]}
    async with httpx.AsyncClient() as client:
        response = await client.post(ollama_url, json=payload, timeout=60.0)
        response.raise_for_status()
        data = response.json()
        answer = data.get("message", data.get("response", ""))

    return {"answer": answer, "sources": sources}



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
    # Check if a page with the same URL already exists
    existing_page = db.query(crud.Page).filter(crud.Page.url == page_data.url).first()
    if existing_page:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Page with URL '{page_data.url}' already exists"
        )
    
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
    embedding_data: EmbeddingCreate,
    db: Session = Depends(get_db)
):
    """
    Add a new embedding vector to an existing page.
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
    - page_type: Filter by page type ('web' or 'pdf')
    - q: Search query text (searches title and URL)
    - limit: Maximum number of results (default: 20, max: 100)
    - offset: Number of results to skip (for pagination)
    """
    return crud.get_pages(db, page_type=page_type, query_text=q, limit=limit, offset=offset)


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



# --- New Semantic Search Endpoint ---
import asyncio
from app.models.models import Page

@router.post(
    "/search/semantic",
    response_model=List[SearchResult],
    tags=["Search"]
)
async def semantic_search(
    request: SemanticSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Perform semantic search over all pages using a text query.
    1. Generate embedding for the query using Ollama.
    2. Use sqlite-vss to find top_k most similar pages.
    3. Return results with page info and similarity score.
    """
    # 1. Generate embedding for the query
    embedding = await get_embedding(request.query)
    if not embedding or len(embedding) != 768:
        raise HTTPException(status_code=500, detail="Failed to generate embedding for query.")

    # 2. Perform vector search
    results = crud.semantic_search(db, embedding, top_k=request.top_k)
    page_ids = [page_id for page_id, _ in results]
    pages = {p.id: p for p in crud.get_pages_by_ids(db, page_ids)}

    # 3. Format results
    search_results = []
    for page_id, score in results:
        page = pages.get(page_id)
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
        

        # Generate embedding using Ollama
        embedding = await get_embedding(result["text"])

        # Prepare page data
        page_data = PageCreate(
            url=url,
            title=result["title"] or title,
            author=result.get("author"),
            publish_date=result.get("publish_date"),
            content_html=result["html"],
            text=result["text"],
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
            page = crud.create_page(db=db, page_data=page_data, embedding=embedding)
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
