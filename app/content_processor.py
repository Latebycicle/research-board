"""
ContentProcessor service for extracting clean text and metadata from raw HTML.
Uses readability-lxml for main content extraction and BeautifulSoup for sanitization.
"""

import hashlib
from typing import Dict, Any, Optional
from readability import Document
from bs4 import BeautifulSoup
import re

class ContentProcessor:
    @staticmethod
    def process(html: str, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Extracts readable text, minimal HTML, and metadata from raw HTML.
        Args:
            html (str): Raw HTML content
            url (str, optional): Source URL for metadata
        Returns:
            dict: {
                'text': Clean plain text,
                'html': Minimal sanitized HTML,
                'title': Title,
                'author': Author (if found),
                'publish_date': Publish date (if found),
                'content_hash': SHA256 hash of text for deduplication
            }
        """
        try:
            # Step 1: Extract main content using readability-lxml
            doc = Document(html)
            title = doc.short_title()
            readable_html = doc.summary(html_partial=True)

            # Step 2: Sanitize HTML with BeautifulSoup
            soup = BeautifulSoup(readable_html, "lxml")
            # Remove unwanted tags
            for tag in soup(["script", "style", "iframe"]):
                tag.decompose()
            # Remove event handler attributes
            for tag in soup.find_all(True):
                attrs = list(tag.attrs.keys())
                for attr in attrs:
                    if re.match(r"on[a-zA-Z]+", attr):
                        del tag.attrs[attr]
            # Minimal HTML for rendering
            minimal_html = str(soup)
            # Extract plain text
            clean_text = soup.get_text(separator="\n", strip=True)

            # Step 3: Extract metadata
            author = None
            publish_date = None
            meta_tags = BeautifulSoup(html, "lxml").find_all("meta")
            for meta in meta_tags:
                name = meta.get("name", "").lower()
                prop = meta.get("property", "").lower()
                if name in ["author", "article:author"] or prop in ["author", "article:author"]:
                    author = meta.get("content")
                if name in ["date", "publishdate", "article:published_time"] or prop in ["date", "publishdate", "article:published_time"]:
                    publish_date = meta.get("content")

            # Step 4: Generate content hash for deduplication
            content_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

            return {
                "text": clean_text,
                "html": minimal_html,
                "title": title,
                "author": author,
                "publish_date": publish_date,
                "content_hash": content_hash
            }
        except Exception as e:
            # Error handling: return error info
            return {
                "error": str(e),
                "text": "",
                "html": "",
                "title": None,
                "author": None,
                "publish_date": None,
                "content_hash": None
            }
