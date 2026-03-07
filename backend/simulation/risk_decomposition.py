"""Risk contribution and decomposition analysis."""

import logging
from typing import Dict, List

import numpy as np

logger = logging.getLogger(__name__)


class RiskDecomposition:
    """Decompose portfolio risk into per-asset contributions."""

    def __init__(
        self,
        weights: np.ndarray,
        covariance_matrix: np.ndarray,
        tickers: List[str],
    ):
        """Initialize risk decomposition.

        Args:
            weights: Array of asset weights (must sum to 1).
            covariance_matrix: Asset covariance matrix.
            tickers: List of asset ticker symbols.
        """
        self.weights = np.array(weights, dtype=float)
        self.cov = np.array(covariance_matrix, dtype=float)
        self.tickers = tickers
        self.n = len(tickers)

    def portfolio_volatility(self) -> float:
        """Calculate total portfolio volatility.

        Returns:
            Portfolio standard deviation (annualized if cov is annualized).
        """
        return float(np.sqrt(self.weights @ self.cov @ self.weights))

    def marginal_risk(self) -> np.ndarray:
        """Calculate marginal risk contribution for each asset.

        Marginal risk = d(portfolio_vol) / d(weight_i)

        Returns:
            Array of marginal risk contributions.
        """
        port_vol = self.portfolio_volatility()
        if port_vol == 0:
            return np.zeros(self.n)
        return (self.cov @ self.weights) / port_vol

    def component_risk(self) -> np.ndarray:
        """Calculate component risk (weight_i * marginal_risk_i).

        Component risks sum to total portfolio volatility.

        Returns:
            Array of component risk contributions.
        """
        return self.weights * self.marginal_risk()

    def percentage_contribution(self) -> np.ndarray:
        """Calculate percentage risk contribution per asset.

        Values sum to 1.0 (or 100%).

        Returns:
            Array of fractional risk contributions.
        """
        port_vol = self.portfolio_volatility()
        if port_vol == 0:
            return np.ones(self.n) / self.n
        return self.component_risk() / port_vol

    def risk_parity_weights(self, max_iter: int = 500, tol: float = 1e-8) -> np.ndarray:
        """Compute risk parity weights (equal risk contribution).

        Uses iterative algorithm to find weights where each asset
        contributes equally to total portfolio risk.

        Args:
            max_iter: Maximum iterations.
            tol: Convergence tolerance.

        Returns:
            Array of risk parity weights.
        """
        w = np.ones(self.n) / self.n

        for _ in range(max_iter):
            port_vol = np.sqrt(w @ self.cov @ w)
            if port_vol == 0:
                break

            marginal = (self.cov @ w) / port_vol
            target_risk = port_vol / self.n

            # Update weights proportional to inverse of marginal risk
            w_new = np.where(marginal > 0, target_risk / marginal, w)
            w_new = w_new / np.sum(w_new)

            if np.max(np.abs(w_new - w)) < tol:
                break
            w = w_new

        return w

    def decompose(self) -> Dict:
        """Full risk decomposition.

        Returns:
            Dictionary with all decomposition results.
        """
        port_vol = self.portfolio_volatility()
        marginal = self.marginal_risk()
        component = self.component_risk()
        pct = self.percentage_contribution()
        rp_weights = self.risk_parity_weights()

        assets = []
        for i, ticker in enumerate(self.tickers):
            assets.append(
                {
                    "ticker": ticker,
                    "weight": round(float(self.weights[i]), 4),
                    "marginal_risk": round(float(marginal[i]), 6),
                    "component_risk": round(float(component[i]), 6),
                    "pct_contribution": round(float(pct[i]) * 100, 2),
                    "risk_parity_weight": round(float(rp_weights[i]), 4),
                }
            )

        # Sort by contribution (highest first)
        assets.sort(key=lambda x: x["pct_contribution"], reverse=True)

        return {
            "portfolio_volatility": round(port_vol, 6),
            "assets": assets,
            "concentration_ratio": round(
                float(np.max(pct) / np.min(pct)) if np.min(pct) > 0 else float("inf"),
                2,
            ),
        }
