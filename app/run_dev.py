#!/usr/bin/env python3
"""
Development server runner for Research Board API.

This script provides a convenient way to run the FastAPI application
during development with hot reloading and proper configuration.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Run the FastAPI application with uvicorn."""
    
    # Load environment variables from .env file if it exists
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"Loading environment variables from {env_file}")
    
    # Configuration
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print(f"Starting Research Board API...")
    print(f"Server: http://{host}:{port}")
    print(f"API Documentation: http://{host}:{port}/api/v1/docs")
    print(f"Debug mode: {debug}")
    
    # Run the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug",
        access_log=True
    )

if __name__ == "__main__":
    main()
