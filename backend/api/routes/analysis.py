"""Analysis API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import pandas as pd
import logging

from backend.database import get_db
from backend.scenarios.scenario_service import ScenarioService

logger = logging.getLogger(__name__)

router = APIRouter()


class ResultsQuery(BaseModel):
    """Query model for results."""
    scenario_id: int = None
    limit: int = 10


@router.get("/results")
async def get_results(
    scenario_id: int = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get scenario simulation results.
    
    Args:
        scenario_id: Optional scenario ID filter
        limit: Maximum number of results
        db: Database session
        
    Returns:
        List of scenario results
    """
    try:
        service = ScenarioService(db)
        results = service.get_scenario_results(
            scenario_id=scenario_id,
            limit=limit
        )
        
        return [
            {
                "id": r.id,
                "scenario_id": r.scenario_id,
                "scenario_name": r.scenario_name,
                "method": r.method,
                "num_simulations": r.num_simulations,
                "num_days": r.num_days,
                "tickers": r.tickers,
                "statistics": r.statistics,
                "var_metrics": r.var_metrics,
                "run_date": r.run_date.isoformat(),
                "execution_time_seconds": r.execution_time_seconds
            }
            for r in results
        ]
        
    except Exception as e:
        logger.error(f"Failed to get results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{result_id}")
async def export_results(
    result_id: int,
    format: str = 'json',
    db: Session = Depends(get_db)
):
    """Export simulation results in various formats.
    
    Args:
        result_id: Result ID
        format: Export format ('json', 'csv')
        db: Database session
        
    Returns:
        Exported data
    """
    try:
        service = ScenarioService(db)
        results = service.get_scenario_results(limit=1000)
        
        # Find the specific result
        result = next((r for r in results if r.id == result_id), None)
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        
        if format == 'json':
            return {
                "scenario_name": result.scenario_name,
                "method": result.method,
                "statistics": result.statistics,
                "var_metrics": result.var_metrics,
                "run_date": result.run_date.isoformat()
            }
        elif format == 'csv':
            # Convert statistics to CSV format
            df = pd.DataFrame(result.statistics)
            csv_data = df.to_csv(index=False)
            return {"csv": csv_data}
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_summary(db: Session = Depends(get_db)):
    """Get summary statistics across all scenarios.
    
    Args:
        db: Database session
        
    Returns:
        Summary statistics
    """
    try:
        service = ScenarioService(db)
        
        # Get all scenarios
        scenarios = service.list_scenarios()
        
        # Get recent results
        results = service.get_scenario_results(limit=100)
        
        # Calculate summary
        summary = {
            "total_scenarios": len(scenarios),
            "predefined_scenarios": len([s for s in scenarios if s.is_predefined]),
            "custom_scenarios": len([s for s in scenarios if not s.is_predefined]),
            "total_simulations_run": len(results),
            "scenarios_by_category": {}
        }
        
        # Group by category
        for scenario in scenarios:
            cat = scenario.category
            summary["scenarios_by_category"][cat] = summary["scenarios_by_category"].get(cat, 0) + 1
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
