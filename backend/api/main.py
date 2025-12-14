"""FastAPI main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from backend.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="API for Cross-Asset Stress Scenario Simulator",
    version="1.0.0",
    debug=settings.debug
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Cross-Asset Stress Scenario Simulator API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import routers
from backend.api.routes import simulation, scenarios, analysis

# Include routers
app.include_router(simulation.router, prefix="/api/simulations", tags=["simulations"])
app.include_router(scenarios.router, prefix="/api/scenarios", tags=["scenarios"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
