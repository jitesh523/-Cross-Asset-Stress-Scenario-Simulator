"""Stress test grid — run scenarios across a parameter grid.

Sweeps across volatility multipliers and correlation levels
simultaneously to map out a risk surface.
"""

import logging
from itertools import product
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class StressGrid:
    """Run stress tests across a 2D parameter grid."""

    def __init__(
        self,
        tickers: List[str],
        base_returns: Dict[str, float],
        base_volatilities: Dict[str, float],
        base_correlation: float = 0.3,
    ):
        """Initialize grid tester.

        Args:
            tickers: Asset ticker symbols.
            base_returns: Dict of ticker → annualized expected return.
            base_volatilities: Dict of ticker → annualized volatility.
            base_correlation: Baseline average pairwise correlation.
        """
        self.tickers = tickers
        self.base_returns = base_returns
        self.base_vols = base_volatilities
        self.base_corr = base_correlation
        self.n = len(tickers)

    def _portfolio_var(self, vol_mult: float, corr: float, weights: np.ndarray) -> float:
        """Compute parametric portfolio VaR at 95% given vol multiplier and correlation."""
        vols = np.array([self.base_vols[t] * vol_mult for t in self.tickers])

        # Build correlation matrix
        corr_matrix = np.full((self.n, self.n), corr)
        np.fill_diagonal(corr_matrix, 1.0)

        # Build covariance matrix
        diag = np.diag(vols)
        cov = diag @ corr_matrix @ diag

        port_vol = float(np.sqrt(weights @ cov @ weights))
        port_return = float(sum(weights[i] * self.base_returns[t] for i, t in enumerate(self.tickers)))

        # Parametric VaR at 95% (1.645 z-score)
        var_95 = port_return - 1.645 * port_vol
        return round(var_95, 6)

    def run(
        self,
        vol_multipliers: Optional[List[float]] = None,
        correlation_levels: Optional[List[float]] = None,
        weights: Optional[np.ndarray] = None,
    ) -> Dict:
        """Run the stress grid.

        Args:
            vol_multipliers: List of volatility multipliers to test.
            correlation_levels: List of correlation levels to test.
            weights: Portfolio weights (defaults to equal weight).

        Returns:
            Dict with grid axes, VaR matrix, and worst/best cases.
        """
        if vol_multipliers is None:
            vol_multipliers = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
        if correlation_levels is None:
            correlation_levels = [0.0, 0.2, 0.4, 0.6, 0.8, 0.95]
        if weights is None:
            weights = np.ones(self.n) / self.n

        matrix = []
        worst_var = float("inf")
        best_var = float("-inf")
        worst_params = {}
        best_params = {}

        for vol_m in vol_multipliers:
            row = []
            for corr in correlation_levels:
                var = self._portfolio_var(vol_m, corr, weights)
                row.append(var)

                if var < worst_var:
                    worst_var = var
                    worst_params = {"vol_multiplier": vol_m, "correlation": corr, "var": var}
                if var > best_var:
                    best_var = var
                    best_params = {"vol_multiplier": vol_m, "correlation": corr, "var": var}

            matrix.append(row)

        return {
            "vol_multipliers": vol_multipliers,
            "correlation_levels": correlation_levels,
            "var_matrix": matrix,
            "worst_case": worst_params,
            "best_case": best_params,
            "grid_size": len(vol_multipliers) * len(correlation_levels),
        }

    def find_breaking_point(
        self,
        var_threshold: float = -0.20,
        weights: Optional[np.ndarray] = None,
    ) -> Dict:
        """Find the parameter combination where VaR exceeds a threshold.

        Useful for answering "how much would vol/correlation need to
        increase before we lose more than X%?"

        Args:
            var_threshold: VaR threshold (e.g. -0.20 means 20% loss).
            weights: Portfolio weights.

        Returns:
            Dict with the first breaking parameter combo, or None if safe.
        """
        if weights is None:
            weights = np.ones(self.n) / self.n

        vol_range = np.arange(1.0, 5.1, 0.25)
        corr_range = np.arange(0.0, 1.0, 0.05)

        for vol_m, corr in product(vol_range, corr_range):
            var = self._portfolio_var(vol_m, round(corr, 2), weights)
            if var < var_threshold:
                return {
                    "threshold": var_threshold,
                    "breaking_vol_multiplier": round(float(vol_m), 2),
                    "breaking_correlation": round(float(corr), 2),
                    "var_at_break": var,
                    "exceeded": True,
                }

        return {
            "threshold": var_threshold,
            "exceeded": False,
            "message": "Portfolio survives all tested parameter combinations",
        }
