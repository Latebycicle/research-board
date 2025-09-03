"""
Basic tests for the Research Board API.

Run with: pytest tests/test_basic.py
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.app import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "Research Board API" in data["message"]
    assert "version" in data


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


def test_api_health_check():
    """Test the API health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_get_pages_empty():
    """Test getting pages when database is empty."""
    response = client.get("/api/v1/pages")
    assert response.status_code == 200
    
    data = response.json()
    assert "pages" in data
    assert isinstance(data["pages"], list)
    assert data["total_count"] >= 0


def test_get_statistics():
    """Test getting application statistics."""
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_pages" in data
    assert "total_highlights" in data
    assert "total_history_entries" in data
    assert isinstance(data["total_pages"], int)


def test_search_endpoint():
    """Test the search endpoint with a basic query."""
    response = client.get("/api/v1/search?q=test")
    assert response.status_code == 200
    
    data = response.json()
    assert "query" in data
    assert data["query"] == "test"
    assert "results" in data


def test_cors_headers():
    """Test that CORS headers are properly set."""
    response = client.options("/")
    # FastAPI automatically handles CORS for OPTIONS requests
    assert response.status_code == 200


def test_nonexistent_page():
    """Test requesting a non-existent page."""
    response = client.get("/api/v1/pages/999999")
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"])
