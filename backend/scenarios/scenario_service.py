"""Scenario management service."""

from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
import logging
import time

from backend.scenarios.scenario_models import Scenario, ScenarioResult
from backend.scenarios.predefined_scenarios import PredefinedScenarios
from backend.simulation.engine import SimulationEngine

logger = logging.getLogger(__name__)


class ScenarioService:
    """Service for managing stress scenarios."""

    def __init__(self, db: Session):
        """Initialize scenario service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.simulation_engine = SimulationEngine(db)

    def create_scenario(
        self,
        name: str,
        description: str,
        category: str,
        parameters: Dict,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None
    ) -> Scenario:
        """Create a new scenario.
        
        Args:
            name: Scenario name (must be unique)
            description: Scenario description
            category: Scenario category
            parameters: Scenario parameters dictionary
            tags: Optional list of tags
            created_by: Optional creator name
            
        Returns:
            Created Scenario object
        """
        logger.info(f"Creating scenario: {name}")
        
        # Check if scenario already exists
        existing = self.db.query(Scenario).filter(Scenario.name == name).first()
        if existing:
            raise ValueError(f"Scenario with name '{name}' already exists")
        
        scenario = Scenario(
            name=name,
            description=description,
            category=category,
            parameters=parameters,
            tags=tags or [],
            created_by=created_by,
            is_predefined=False
        )
        
        self.db.add(scenario)
        self.db.commit()
        self.db.refresh(scenario)
        
        logger.info(f"Scenario created with ID: {scenario.id}")
        return scenario

    def get_scenario(self, scenario_id: int) -> Optional[Scenario]:
        """Get a scenario by ID.
        
        Args:
            scenario_id: Scenario ID
            
        Returns:
            Scenario object or None if not found
        """
        return self.db.query(Scenario).filter(Scenario.id == scenario_id).first()

    def get_scenario_by_name(self, name: str) -> Optional[Scenario]:
        """Get a scenario by name.
        
        Args:
            name: Scenario name
            
        Returns:
            Scenario object or None if not found
        """
        return self.db.query(Scenario).filter(Scenario.name == name).first()

    def list_scenarios(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_predefined: Optional[bool] = None
    ) -> List[Scenario]:
        """List scenarios with optional filtering.
        
        Args:
            category: Optional category filter
            tags: Optional tags filter (scenarios with any of these tags)
            is_predefined: Optional filter for predefined scenarios
            
        Returns:
            List of Scenario objects
        """
        query = self.db.query(Scenario)
        
        if category:
            query = query.filter(Scenario.category == category)
        
        if is_predefined is not None:
            query = query.filter(Scenario.is_predefined == is_predefined)
        
        scenarios = query.all()
        
        # Filter by tags if provided
        if tags:
            scenarios = [
                s for s in scenarios
                if s.tags and any(tag in s.tags for tag in tags)
            ]
        
        return scenarios

    def update_scenario(
        self,
        scenario_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> Scenario:
        """Update an existing scenario.
        
        Args:
            scenario_id: Scenario ID
            name: Optional new name
            description: Optional new description
            parameters: Optional new parameters
            tags: Optional new tags
            
        Returns:
            Updated Scenario object
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario with ID {scenario_id} not found")
        
        if scenario.is_predefined:
            raise ValueError("Cannot update predefined scenarios")
        
        if name:
            scenario.name = name
        if description:
            scenario.description = description
        if parameters:
            scenario.parameters = parameters
        if tags is not None:
            scenario.tags = tags
        
        scenario.version += 1
        scenario.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(scenario)
        
        logger.info(f"Scenario {scenario_id} updated to version {scenario.version}")
        return scenario

    def delete_scenario(self, scenario_id: int):
        """Delete a scenario.
        
        Args:
            scenario_id: Scenario ID
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario with ID {scenario_id} not found")
        
        if scenario.is_predefined:
            raise ValueError("Cannot delete predefined scenarios")
        
        self.db.delete(scenario)
        self.db.commit()
        
        logger.info(f"Scenario {scenario_id} deleted")

    def load_predefined_scenarios(self):
        """Load all predefined scenarios into the database."""
        logger.info("Loading predefined scenarios")
        
        predefined = PredefinedScenarios.get_all_scenarios()
        loaded_count = 0
        
        for scenario_dict in predefined:
            # Check if already exists
            existing = self.get_scenario_by_name(scenario_dict["name"])
            if existing:
                logger.info(f"Scenario '{scenario_dict['name']}' already exists, skipping")
                continue
            
            scenario = Scenario(
                name=scenario_dict["name"],
                description=scenario_dict["description"],
                category=scenario_dict["category"],
                parameters=scenario_dict["parameters"],
                tags=scenario_dict["tags"],
                is_predefined=scenario_dict["is_predefined"]
            )
            
            self.db.add(scenario)
            loaded_count += 1
        
        self.db.commit()
        logger.info(f"Loaded {loaded_count} predefined scenarios")

    def run_scenario(
        self,
        scenario_id: int,
        tickers: List[str],
        start_date: str,
        end_date: str,
        method: str = 'monte_carlo',
        num_simulations: int = 1000,
        num_days: int = 252,
        **kwargs
    ) -> Dict:
        """Run a simulation with a specific scenario.
        
        Args:
            scenario_id: Scenario ID
            tickers: List of ticker symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            method: Simulation method ('monte_carlo' or 'historical')
            num_simulations: Number of simulation paths
            num_days: Number of days to simulate
            **kwargs: Additional simulation parameters
            
        Returns:
            Dictionary with simulation results
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario with ID {scenario_id} not found")
        
        logger.info(f"Running scenario: {scenario.name}")
        
        start_time = time.time()
        
        # Run simulation with scenario adjustments
        if method == 'monte_carlo':
            results = self.simulation_engine.run_monte_carlo(
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                num_simulations=num_simulations,
                num_days=num_days,
                scenario_adjustments=scenario.parameters,
                **kwargs
            )
        elif method == 'historical':
            results = self.simulation_engine.run_historical(
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                num_simulations=num_simulations,
                num_days=num_days,
                **kwargs
            )
        else:
            raise ValueError(f"Unknown simulation method: {method}")
        
        execution_time = time.time() - start_time
        
        # Save results
        scenario_result = ScenarioResult(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            method=method,
            num_simulations=num_simulations,
            num_days=num_days,
            tickers=tickers,
            statistics=results['statistics'].to_dict('records'),
            var_metrics=results['var_metrics'],
            execution_time_seconds=execution_time
        )
        
        self.db.add(scenario_result)
        self.db.commit()
        
        logger.info(f"Scenario simulation completed in {execution_time:.2f}s")
        
        return {
            **results,
            'scenario': {
                'id': scenario.id,
                'name': scenario.name,
                'description': scenario.description,
                'category': scenario.category
            },
            'execution_time': execution_time
        }

    def get_scenario_results(
        self,
        scenario_id: Optional[int] = None,
        limit: int = 10
    ) -> List[ScenarioResult]:
        """Get scenario simulation results.
        
        Args:
            scenario_id: Optional scenario ID filter
            limit: Maximum number of results to return
            
        Returns:
            List of ScenarioResult objects
        """
        query = self.db.query(ScenarioResult)
        
        if scenario_id:
            query = query.filter(ScenarioResult.scenario_id == scenario_id)
        
        query = query.order_by(ScenarioResult.run_date.desc()).limit(limit)
        
        return query.all()
