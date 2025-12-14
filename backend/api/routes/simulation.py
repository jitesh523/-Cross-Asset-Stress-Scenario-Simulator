"""Simulation API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging

from backend.database import get_db
from backend.simulation.engine import SimulationEngine

logger = logging.getLogger(__name__)

router = APIRouter()


class SimulationRequest(BaseModel):
    """Request model for running simulations."""
    method: str  # 'monte_carlo' or 'historical'
    tickers: List[str]
    start_date: str
    end_date: str
    num_simulations: int = 1000
    num_days: int = 252
    use_correlation: Optional[bool] = True
    block_size: Optional[int] = 1
    random_seed: Optional[int] = None


class SimulationResponse(BaseModel):
    """Response model for simulation results."""
    method: str
    statistics: List[dict]
    var_metrics: dict
    parameters: dict


@router.post("/run", response_model=SimulationResponse)
async def run_simulation(
    request: SimulationRequest,
    db: Session = Depends(get_db)
):
    """Run a simulation.
    
    Args:
        request: Simulation parameters
        db: Database session
        
    Returns:
        Simulation results
    """
    try:
        logger.info(f"Running {request.method} simulation for {len(request.tickers)} tickers")
        
        engine = SimulationEngine(db)
        
        results = engine.run_simulation(
            method=request.method,
            tickers=request.tickers,
            start_date=request.start_date,
            end_date=request.end_date,
            num_simulations=request.num_simulations,
            num_days=request.num_days,
            use_correlation=request.use_correlation,
            block_size=request.block_size,
            random_seed=request.random_seed
        )
        
        return SimulationResponse(
            method=results['method'],
            statistics=results['statistics'].to_dict('records'),
            var_metrics=results['var_metrics'],
            parameters=results['parameters']
        )
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_methods(
    tickers: List[str],
    start_date: str,
    end_date: str,
    num_simulations: int = 1000,
    num_days: int = 252,
    db: Session = Depends(get_db)
):
    """Compare Monte Carlo and Historical simulation methods.
    
    Args:
        tickers: List of ticker symbols
        start_date: Start date for historical data
        end_date: End date for historical data
        num_simulations: Number of simulations
        num_days: Number of days to simulate
        db: Database session
        
    Returns:
        Comparison results
    """
    try:
        engine = SimulationEngine(db)
        
        comparison = engine.compare_methods(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            num_simulations=num_simulations,
            num_days=num_days
        )
        
        return comparison
        
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
