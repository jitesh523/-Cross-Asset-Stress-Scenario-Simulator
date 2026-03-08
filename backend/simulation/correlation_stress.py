"""Correlation stress testing utility.

Simulates how portfolio risk changes when correlations shift,
for example during a crisis when assets become more correlated.
"""

import logging
from typing import Dict, List

import numpy as np

from backend.simulation.utils import make_positive_definite

logger = logging.getLogger(__name__)


class CorrelationStressTester:
    """Test portfolio sensitivity to correlation changes."""

    def __init__(
        self,
        correlation_matrix: np.ndarray,
        volatilities: np.ndarray,
        weights: np.ndarray,
        tickers: List[str],
    ):
        """Initialize with baseline portfolio parameters.

        Args:
            correlation_matrix: Baseline correlation matrix.
            volatilities: Asset volatilities.
            weights: Portfolio weights.
            tickers: Asset ticker symbols.
        """
        self.base_corr = correlation_matrix
        self.vols = volatilities
        self.weights = weights
        self.tickers = tickers
        self.n = len(tickers)

    def _portfolio_vol(self, corr: np.ndarray) -> float:
        """Calculate portfolio volatility given a correlation matrix."""
        diag = np.diag(self.vols)
        cov = diag @ corr @ diag
        return float(np.sqrt(self.weights @ cov @ self.weights))

    def stress_uniform(self, shifts: List[float] = None) -> List[Dict]:
        """Apply uniform correlation shifts and measure the impact.

        Increases all off-diagonal correlations by the given amounts.

        Args:
            shifts: List of correlation shifts to test (e.g. [0.1, 0.2, 0.5]).

        Returns:
            List of results for each shift level.
        """
        if shifts is None:
            shifts = [0.1, 0.2, 0.3, 0.5]

        base_vol = self._portfolio_vol(self.base_corr)
        results = []

        for shift in shifts:
            stressed = self.base_corr.copy()
            for i in range(self.n):
                for j in range(self.n):
                    if i != j:
                        stressed[i, j] = min(stressed[i, j] + shift, 1.0)

            stressed = make_positive_definite(stressed)
            stressed_vol = self._portfolio_vol(stressed)
            vol_change = (stressed_vol - base_vol) / base_vol

            results.append(
                {
                    "correlation_shift": shift,
                    "baseline_vol": round(base_vol, 6),
                    "stressed_vol": round(stressed_vol, 6),
                    "vol_change_pct": round(vol_change * 100, 2),
                }
            )

        return results

    def stress_to_one(self) -> Dict:
        """Test the extreme case: all correlations go to 1.

        Returns:
            Impact of perfect correlation.
        """
        base_vol = self._portfolio_vol(self.base_corr)
        perfect_corr = np.ones((self.n, self.n))
        worst_vol = self._portfolio_vol(perfect_corr)
        vol_change = (worst_vol - base_vol) / base_vol

        return {
            "scenario": "perfect_correlation",
            "baseline_vol": round(base_vol, 6),
            "worst_case_vol": round(worst_vol, 6),
            "vol_increase_pct": round(vol_change * 100, 2),
        }

    def sensitivity_matrix(self) -> Dict:
        """Calculate how much portfolio vol changes when each pair's
        correlation increases by 0.1.

        Returns:
            Dict with pair sensitivities.
        """
        base_vol = self._portfolio_vol(self.base_corr)
        pairs = []

        for i in range(self.n):
            for j in range(i + 1, self.n):
                stressed = self.base_corr.copy()
                stressed[i, j] = min(stressed[i, j] + 0.1, 1.0)
                stressed[j, i] = stressed[i, j]
                stressed = make_positive_definite(stressed)

                new_vol = self._portfolio_vol(stressed)
                impact = (new_vol - base_vol) / base_vol

                pairs.append(
                    {
                        "pair": f"{self.tickers[i]}/{self.tickers[j]}",
                        "base_correlation": round(float(self.base_corr[i, j]), 4),
                        "vol_impact_pct": round(impact * 100, 4),
                    }
                )

        pairs.sort(key=lambda x: abs(x["vol_impact_pct"]), reverse=True)
        return {
            "baseline_vol": round(base_vol, 6),
            "pair_sensitivities": pairs,
        }
