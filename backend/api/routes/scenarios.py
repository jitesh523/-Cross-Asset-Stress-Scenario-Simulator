"""Scenario API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging

from backend.database import get_db
from backend.scenarios.scenario_service import ScenarioService
from backend.scenarios.predefined_scenarios import PredefinedScenarios
from backend.scenarios.ai_engine import AIScenarioEngine

logger = logging.getLogger(__name__)

router = APIRouter()


class ScenarioCreate(BaseModel):
    """Request model for creating scenarios."""
    name: str
    description: str
    category: str
    parameters: dict
    tags: Optional[List[str]] = []


class ScenarioResponse(BaseModel):
    """Response model for scenarios."""
    id: int
    name: str
    description: str
    category: str
    parameters: dict
    tags: List[str]
    is_predefined: bool
    version: int
    
    class Config:
        from_attributes = True


class ScenarioRunRequest(BaseModel):
    """Request model for running scenarios."""
    tickers: List[str]
    start_date: str
    end_date: str
    method: str = 'monte_carlo'
    num_simulations: int = 1000
    num_days: int = 252
    regime_aware: Optional[bool] = False


class AIGenerateRequest(BaseModel):
    """Request model for AI scenario generation."""
    prompt: str
    provider: Optional[str] = "openai"


@router.get("/", response_model=List[ScenarioResponse])
async def list_scenarios(
    category: Optional[str] = None,
    is_predefined: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all scenarios with optional filtering.
    
    Args:
        category: Optional category filter
        is_predefined: Optional predefined filter
        db: Database session
        
    Returns:
        List of scenarios
    """
    try:
        service = ScenarioService(db)
        scenarios = service.list_scenarios(
            category=category,
            is_predefined=is_predefined
        )
        return scenarios
        
    except Exception as e:
        logger.error(f"Failed to list scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predefined")
async def get_predefined_scenarios():
    """Get all predefined scenarios (without database).
    
    Returns:
        List of predefined scenario definitions
    """
    try:
        scenarios = PredefinedScenarios.get_all_scenarios()
        return scenarios
        
    except Exception as e:
        logger.error(f"Failed to get predefined scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load-predefined")
async def load_predefined_scenarios(db: Session = Depends(get_db)):
    """Load predefined scenarios into database.
    
    Args:
        db: Database session
        
    Returns:
        Success message
    """
    try:
        service = ScenarioService(db)
        service.load_predefined_scenarios()
        return {"message": "Predefined scenarios loaded successfully"}
        
    except Exception as e:
        logger.error(f"Failed to load predefined scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: int, db: Session = Depends(get_db)):
    """Get a specific scenario by ID.
    
    Args:
        scenario_id: Scenario ID
        db: Database session
        
    Returns:
        Scenario details
    """
    try:
        service = ScenarioService(db)
        scenario = service.get_scenario(scenario_id)
        
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        return scenario
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=ScenarioResponse)
async def create_scenario(
    scenario: ScenarioCreate,
    db: Session = Depends(get_db)
):
    """Create a new custom scenario.
    
    Args:
        scenario: Scenario data
        db: Database session
        
    Returns:
        Created scenario
    """
    try:
        service = ScenarioService(db)
        created = service.create_scenario(
            name=scenario.name,
            description=scenario.description,
            category=scenario.category,
            parameters=scenario.parameters,
            tags=scenario.tags
        )
        return created
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-ai")
async def generate_ai_scenario(
    request: AIGenerateRequest,
    db: Session = Depends(get_db)
):
    """Generate a scenario using AI.
    
    Args:
        request: AI generation parameters
        db: Database session
        
    Returns:
        Generated scenario parameters
    """
    try:
        # Get available tickers for context
        # In a real app, this would come from a registry or database
        available_assets = [
            "SPY", "QQQ", "DIA", "IWM", "AAPL", "MSFT", "GOOGL", "AMZN",
            "TLT", "IEF", "SHY", "LQD", "HYG",
            "GLD", "SLV", "USO", "DBA",
            "EUR/USD", "GBP/USD", "JPY/USD", "AUD/USD"
        ]
        
        engine = AIScenarioEngine(provider=request.provider)
        result = engine.generate_scenario_params(request.prompt, available_assets)
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate AI scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{scenario_id}/run")
async def run_scenario(
    scenario_id: int,
    request: ScenarioRunRequest,
    db: Session = Depends(get_db)
):
    """Run a simulation with a specific scenario.
    
    Args:
        scenario_id: Scenario ID
        request: Simulation parameters
        db: Database session
        
    Returns:
        Simulation results
    """
    try:
        service = ScenarioService(db)
        
        results = service.run_scenario(
            scenario_id=scenario_id,
            tickers=request.tickers,
            start_date=request.start_date,
            end_date=request.end_date,
            method=request.method,
            num_simulations=request.num_simulations,
            num_days=request.num_days,
            regime_aware=request.regime_aware
        )
        
        return results
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to run scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{scenario_id}")
async def delete_scenario(scenario_id: int, db: Session = Depends(get_db)):
    """Delete a custom scenario.
    
    Args:
        scenario_id: Scenario ID
        db: Database session
        
    Returns:
        Success message
    """
    try:
        service = ScenarioService(db)
        service.delete_scenario(scenario_id)
        return {"message": "Scenario deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))
