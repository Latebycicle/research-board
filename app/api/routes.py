"""
API routes for the Research Board application.

This module defines the main API router and route handlers for handling
web page data, highlights, history, and search functionality.
"""

from fastapi import APIRouter, Request, status, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.content_processor import ContentProcessor
from app.db.database import get_db
from app.models.models import Page
from sqlalchemy.orm import Session
import logging

router = APIRouter()

@router.get("/health", tags=["health"])
async def api_health():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "service": "research-board-api"
    }

@router.post("/collect", tags=["collect"])
async def collect_content(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint to process and store incoming raw HTML content from extension.
    Expects JSON: {"html": ..., "url": ..., "title": ..., "meta": ..., "images": ..., "text": ..., "accessedAt": ...}
    Returns processed text, minimal HTML, and metadata.
    """
    try:
        data = await request.json()
        logging.info(f"[ResearchBoard] Received /collect payload: {data}")
        html = data.get("html")
        url = data.get("url")
        title = data.get("title")
        meta = data.get("meta")
        images = data.get("images")
        raw_text = data.get("text")
        accessed_at = data.get("accessedAt")
        if not html or not url:
            logging.error(f"[ResearchBoard] Missing html or url in payload: {data}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing html or url")
        result = ContentProcessor.process(html, url)
        logging.info(f"[ResearchBoard] Cleaned HTML:\n{result['text']}")
        if result.get("error"):
            logging.error(f"[ResearchBoard] ContentProcessor error: {result['error']}")
            return JSONResponse(status_code=400, content={"error": result["error"]})
        # Store processed content in the database
        page = Page(
            url=url,
            title=result["title"] or title,
            content=result["text"]
        )
        db.add(page)
        db.commit()
        db.refresh(page)
        logging.info(f"[ResearchBoard] Stored page id {page.id} for url {url}")
        return {
            "success": True,
            "page_id": page.id,
            "title": result["title"] or title,
            "author": result["author"],
            "publish_date": result["publish_date"],
            "content_hash": result["content_hash"],
            "text": result["text"],
            "html": result["html"],
            "meta": meta,
            "images": images,
            "raw_text": raw_text,
            "accessed_at": accessed_at
        }
    except Exception as e:
        logging.error(f"[ResearchBoard] Exception in /collect: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
