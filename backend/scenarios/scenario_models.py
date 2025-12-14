"""Scenario database models."""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from backend.database.models import Base


class Scenario(Base):
    """Stress scenario definition."""

    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(String(1000))
    category = Column(String(50), index=True)  # market_crash, rate_shock, volatility_spike, etc.
    
    # Scenario parameters stored as JSON
    parameters = Column(JSON, nullable=False)
    # Example structure:
    # {
    #   "return_shocks": {"SPY": -0.20, "TLT": 0.05},
    #   "volatility_multipliers": {"SPY": 1.5, "TLT": 1.2},
    #   "correlation_multiplier": 1.3
    # }
    
    # Metadata
    is_predefined = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    
    # Tags for categorization
    tags = Column(JSON)  # List of tags: ["historical", "severe", "equity"]

    def __repr__(self):
        return f"<Scenario(name={self.name}, category={self.category})>"


class ScenarioResult(Base):
    """Results from running a scenario simulation."""

    __tablename__ = "scenario_results"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, nullable=False, index=True)
    scenario_name = Column(String(200), nullable=False)
    
    # Simulation parameters
    method = Column(String(50))  # monte_carlo or historical
    num_simulations = Column(Integer)
    num_days = Column(Integer)
    tickers = Column(JSON)  # List of tickers used
    
    # Results summary (stored as JSON)
    statistics = Column(JSON)
    var_metrics = Column(JSON)
    
    # Metadata
    run_date = Column(DateTime, default=datetime.utcnow, index=True)
    execution_time_seconds = Column(Float)
    
    def __repr__(self):
        return f"<ScenarioResult(scenario={self.scenario_name}, method={self.method})>"
