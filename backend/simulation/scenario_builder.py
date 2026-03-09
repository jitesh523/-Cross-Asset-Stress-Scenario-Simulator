"""Scenario builder for creating custom stress scenarios programmatically."""

import logging
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ScenarioBuilder:
    """Build custom stress scenarios with a fluent API."""

    def __init__(self, name: str):
        """Initialize a new scenario.

        Args:
            name: Descriptive name for the scenario.
        """
        self.name = name
        self.description = ""
        self.shocks: Dict[str, Dict] = {}
        self.correlation_override: Optional[float] = None
        self.volatility_multiplier: float = 1.0
        self.duration_days: int = 252

    def set_description(self, desc: str) -> "ScenarioBuilder":
        """Set scenario description."""
        self.description = desc
        return self

    def add_shock(self, ticker: str, return_shock: float, vol_shock: float = 0.0) -> "ScenarioBuilder":
        """Add a return shock to a specific asset.

        Args:
            ticker: Asset ticker.
            return_shock: Expected return change (decimal, e.g. -0.30 for -30%).
            vol_shock: Volatility increase (decimal, e.g. 0.5 for +50% vol).

        Returns:
            Self for chaining.
        """
        self.shocks[ticker] = {
            "return_shock": return_shock,
            "vol_shock": vol_shock,
        }
        return self

    def set_correlation_stress(self, target: float) -> "ScenarioBuilder":
        """Set all correlations to a target value (simulates contagion).

        Args:
            target: Target correlation for all pairs (e.g. 0.8).

        Returns:
            Self for chaining.
        """
        self.correlation_override = target
        return self

    def set_vol_multiplier(self, multiplier: float) -> "ScenarioBuilder":
        """Multiply all volatilities by a factor.

        Args:
            multiplier: Volatility multiplier (e.g. 2.0 for double vol).

        Returns:
            Self for chaining.
        """
        self.volatility_multiplier = multiplier
        return self

    def set_duration(self, days: int) -> "ScenarioBuilder":
        """Set simulation duration.

        Args:
            days: Number of trading days.

        Returns:
            Self for chaining.
        """
        self.duration_days = days
        return self

    def build(self) -> Dict:
        """Build the scenario specification.

        Returns:
            Complete scenario dict ready for the simulation engine.
        """
        return {
            "name": self.name,
            "description": self.description,
            "shocks": self.shocks,
            "correlation_override": self.correlation_override,
            "volatility_multiplier": self.volatility_multiplier,
            "duration_days": self.duration_days,
            "num_shocks": len(self.shocks),
        }

    def validate(self) -> List[str]:
        """Validate the scenario for common issues.

        Returns:
            List of warning messages (empty if valid).
        """
        warnings = []

        if not self.shocks:
            warnings.append("No asset shocks defined")

        for ticker, shock in self.shocks.items():
            ret = shock["return_shock"]
            if ret < -1.0:
                warnings.append(f"{ticker}: return shock {ret} is below -100%")
            if ret > 2.0:
                warnings.append(f"{ticker}: return shock {ret} exceeds +200%")
            if shock["vol_shock"] < -1.0:
                warnings.append(f"{ticker}: vol shock would make volatility negative")

        if self.correlation_override is not None:
            if not -1.0 <= self.correlation_override <= 1.0:
                warnings.append(f"Correlation override {self.correlation_override} out of [-1, 1] range")

        if self.volatility_multiplier <= 0:
            warnings.append("Volatility multiplier must be positive")

        return warnings


def build_crisis_scenario(tickers: List[str], severity: float = 0.5) -> Dict:
    """Convenience function to build a generic crisis scenario.

    Args:
        tickers: List of asset tickers.
        severity: Crisis severity from 0 (mild) to 1 (extreme).

    Returns:
        Scenario specification dict.
    """
    builder = ScenarioBuilder(f"Crisis (severity={severity})")
    builder.set_description(f"Auto-generated crisis scenario with {severity:.0%} severity")
    builder.set_vol_multiplier(1.0 + severity * 2.0)
    builder.set_correlation_stress(min(0.3 + severity * 0.6, 0.95))

    for ticker in tickers:
        shock = -severity * (0.2 + np.random.uniform(0, 0.2))
        vol_add = severity * np.random.uniform(0.3, 0.8)
        builder.add_shock(ticker, round(shock, 4), round(vol_add, 4))

    return builder.build()
