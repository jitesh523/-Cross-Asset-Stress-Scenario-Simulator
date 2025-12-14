"""Script to run the FastAPI server."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from backend.api.main import app

if __name__ == "__main__":
    print("=" * 60)
    print("Cross-Asset Stress Scenario Simulator - API Server")
    print("=" * 60)
    print("\nStarting FastAPI server...")
    print("API Documentation: http://localhost:8000/docs")
    print("Dashboard: Open frontend/index.html in your browser")
    print("\nPress CTRL+C to stop the server")
    print("=" * 60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
