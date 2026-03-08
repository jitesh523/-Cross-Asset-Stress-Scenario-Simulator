"""Simulation API routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.simulation.engine import SimulationEngine
from backend.simulation.hedging_service import HedgingService
from backend.simulation.optimizer import PortfolioOptimizer
from backend.simulation.report_generator import StressTestReport

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
    regime_aware: Optional[bool] = False


class OptimizationRequest(BaseModel):
    """Request model for portfolio optimization."""

    tickers: List[str]
    start_date: str
    end_date: str
    scenario_adjustments: Optional[dict] = None


class SimulationResponse(BaseModel):
    """Response model for simulation results."""

    method: str
    statistics: List[dict]
    var_metrics: dict
    parameters: dict


@router.post("/run", response_model=SimulationResponse)
async def run_simulation(request: SimulationRequest, db: Session = Depends(get_db)):
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
            random_seed=request.random_seed,
        )

        return SimulationResponse(
            method=results["method"],
            statistics=results["statistics"].to_dict("records"),
            var_metrics=results["var_metrics"],
            parameters=results["parameters"],
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
    db: Session = Depends(get_db),
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
            num_days=num_days,
        )

        return comparison

    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize")
async def optimize_portfolio(request: OptimizationRequest, db: Session = Depends(get_db)):
    """Optimize portfolio weights.

    Args:
        request: Optimization parameters
        db: Database session

    Returns:
        Optimal weights for Max Sharpe and Min Volatility
    """
    try:
        engine = SimulationEngine(db)

        # Prepare data
        data = engine.prepare_simulation_data(request.tickers, request.start_date, request.end_date)

        # Apply scenario adjustments if provided
        if request.scenario_adjustments:
            data = engine._apply_scenario_adjustments(data, request.scenario_adjustments)

        # Initialize optimizer
        optimizer = PortfolioOptimizer(
            expected_returns=data["expected_returns"],
            correlation_matrix=data["correlation_matrix"],
            volatilities=data["volatilities"],
        )

        # Run optimizations
        max_sharpe = optimizer.optimize_maximum_sharpe()
        min_vol = optimizer.optimize_minimum_volatility()

        # Generate hedging suggestions for Min Volatility by default
        hedger = HedgingService(request.tickers)
        suggestions = hedger.generate_recommendations(min_vol)

        return {
            "max_sharpe": max_sharpe,
            "min_volatility": min_vol,
            "hedging_suggestions": suggestions,
            "tickers": request.tickers,
        }

    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ReportRequest(BaseModel):
    """Request model for stress test report."""

    tickers: List[str]
    start_date: str
    end_date: str
    scenario_name: str = "Custom Scenario"
    num_simulations: int = 1000
    num_days: int = 252
    scenario_adjustments: Optional[dict] = None


@router.post("/report")
async def generate_report(request: ReportRequest, db: Session = Depends(get_db)):
    """Run a simulation and generate a stress test report.

    Args:
        request: Report parameters
        db: Database session

    Returns:
        Structured stress test report
    """
    try:
        engine = SimulationEngine(db)

        results = engine.run_simulation(
            method="monte_carlo",
            tickers=request.tickers,
            start_date=request.start_date,
            end_date=request.end_date,
            num_simulations=request.num_simulations,
            num_days=request.num_days,
            scenario_adjustments=request.scenario_adjustments,
        )

        report = StressTestReport(
            simulation_stats=results["statistics"].to_dict("records"),
            var_metrics=results["var_metrics"],
            scenario_name=request.scenario_name,
            parameters=results["parameters"],
        )

        return report.generate()

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
