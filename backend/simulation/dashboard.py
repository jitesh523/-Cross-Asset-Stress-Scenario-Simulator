"""Dashboard data aggregator.

Collects outputs from multiple analytics modules
into a single response for frontend consumption.
"""

import logging
from typing import Dict, List

import numpy as np
import pandas as pd

from backend.simulation.risk_metrics import RiskMetrics
from backend.simulation.vol_term_structure import VolatilityTermStructure

logger = logging.getLogger(__name__)


class DashboardAggregator:
    """Aggregate all analytics into a single dashboard payload."""

    def __init__(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float],
        prices: pd.DataFrame = None,
    ):
        """Initialize aggregator.

        Args:
            returns: DataFrame of daily returns.
            weights: Dict of ticker → portfolio weight.
            prices: Optional DataFrame of prices (for risk metrics).
        """
        self.returns = returns
        self.weights = weights
        self.tickers = list(returns.columns)
        self.prices = prices

    def portfolio_returns(self) -> pd.Series:
        """Compute the portfolio return series."""
        w = np.array([self.weights.get(t, 0) for t in self.tickers])
        return (self.returns * w).sum(axis=1)

    def summary_stats(self) -> Dict:
        """Key portfolio-level statistics."""
        port_ret = self.portfolio_returns()
        ann_return = float(port_ret.mean() * 252)
        ann_vol = float(port_ret.std() * np.sqrt(252))
        sharpe = ann_return / ann_vol if ann_vol > 0 else 0.0

        # VaR and CVaR at 95%
        var_95 = float(np.percentile(port_ret, 5))
        cvar_95 = float(port_ret[port_ret <= var_95].mean()) if (port_ret <= var_95).any() else var_95

        return {
            "annualized_return": round(ann_return * 100, 2),
            "annualized_volatility": round(ann_vol * 100, 2),
            "sharpe_ratio": round(sharpe, 4),
            "daily_var_95": round(var_95 * 100, 4),
            "daily_cvar_95": round(cvar_95 * 100, 4),
            "num_observations": len(port_ret),
        }

    def per_asset_stats(self) -> List[Dict]:
        """Per-asset statistics."""
        assets = []
        for t in self.tickers:
            col = self.returns[t]
            ann_ret = float(col.mean() * 252)
            ann_vol = float(col.std() * np.sqrt(252))
            sharpe = ann_ret / ann_vol if ann_vol > 0 else 0.0

            assets.append(
                {
                    "ticker": t,
                    "weight": round(self.weights.get(t, 0), 4),
                    "annualized_return": round(ann_ret * 100, 2),
                    "annualized_volatility": round(ann_vol * 100, 2),
                    "sharpe_ratio": round(sharpe, 4),
                    "min_daily_return": round(float(col.min()) * 100, 4),
                    "max_daily_return": round(float(col.max()) * 100, 4),
                }
            )

        assets.sort(key=lambda x: x["sharpe_ratio"], reverse=True)
        return assets

    def risk_metrics_summary(self) -> Dict:
        """Compute risk metrics for the portfolio."""
        port_ret = self.portfolio_returns()
        prices_series = (1 + port_ret).cumprod() * 1000  # Synthetic price series

        return RiskMetrics.compute_all(prices_series.values, port_ret.values)

    def vol_structure(self) -> Dict:
        """Get volatility term structure."""
        return VolatilityTermStructure(self.returns).term_structure(windows=[5, 21, 63, 252])

    def generate(self) -> Dict:
        """Generate the full dashboard payload.

        Returns:
            Dict with all aggregated analytics.
        """
        return {
            "portfolio_summary": self.summary_stats(),
            "risk_metrics": self.risk_metrics_summary(),
            "per_asset": self.per_asset_stats(),
            "vol_term_structure": self.vol_structure(),
        }
