"""Multi-period rebalancing simulator.

Simulates portfolio evolution across multiple rebalancing periods,
tracking drift, turnover, and cumulative performance.
"""

import logging
from typing import Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)


class RebalancingSimulator:
    """Simulate portfolio over multiple rebalancing periods."""

    def __init__(
        self,
        target_weights: Dict[str, float],
        expected_returns: Dict[str, float],
        volatilities: Dict[str, float],
        initial_value: float = 1000000.0,
    ):
        """Initialize simulator.

        Args:
            target_weights: Dict of ticker → target weight.
            expected_returns: Dict of ticker → annualized return.
            volatilities: Dict of ticker → annualized volatility.
            initial_value: Starting portfolio value in dollars.
        """
        self.tickers = sorted(target_weights.keys())
        self.target = target_weights
        self.returns = expected_returns
        self.vols = volatilities
        self.initial_value = initial_value

    def simulate(
        self,
        num_periods: int = 12,
        days_per_period: int = 21,
        rebalance: bool = True,
        drift_threshold: float = 0.05,
        seed: Optional[int] = None,
    ) -> Dict:
        """Run multi-period simulation.

        Args:
            num_periods: Number of rebalancing periods.
            days_per_period: Trading days per period.
            rebalance: Whether to rebalance at end of each period.
            drift_threshold: Only rebalance if drift exceeds this.
            seed: Random seed for reproducibility.

        Returns:
            Dict with period-by-period results.
        """
        if seed is not None:
            np.random.seed(seed)

        weights = {t: self.target[t] for t in self.tickers}
        portfolio_value = self.initial_value
        periods = []
        total_turnover = 0.0

        for period in range(num_periods):
            # Simulate returns for this period
            period_returns = {}
            for t in self.tickers:
                daily_mu = self.returns[t] / 252
                daily_sigma = self.vols[t] / np.sqrt(252)
                daily_rets = np.random.normal(daily_mu, daily_sigma, days_per_period)
                period_returns[t] = float(np.prod(1 + daily_rets) - 1)

            # Compute new portfolio value
            weighted_return = sum(weights[t] * period_returns[t] for t in self.tickers)
            portfolio_value *= 1 + weighted_return

            # Compute drifted weights after returns
            total_drifted = sum(weights[t] * (1 + period_returns[t]) for t in self.tickers)
            drifted = {t: weights[t] * (1 + period_returns[t]) / total_drifted for t in self.tickers}

            # Compute drift
            max_drift = max(abs(drifted[t] - self.target[t]) for t in self.tickers)

            # Rebalance if needed
            did_rebalance = False
            turnover = 0.0
            if rebalance and max_drift > drift_threshold:
                turnover = sum(abs(drifted[t] - self.target[t]) for t in self.tickers) / 2
                total_turnover += turnover
                weights = {t: self.target[t] for t in self.tickers}
                did_rebalance = True
            else:
                weights = drifted

            periods.append(
                {
                    "period": period + 1,
                    "portfolio_value": round(portfolio_value, 2),
                    "period_return": round(weighted_return * 100, 2),
                    "max_drift": round(max_drift * 100, 2),
                    "rebalanced": did_rebalance,
                    "turnover": round(turnover * 100, 2),
                    "weights": {t: round(weights[t], 4) for t in self.tickers},
                }
            )

        total_return = (portfolio_value - self.initial_value) / self.initial_value

        return {
            "initial_value": self.initial_value,
            "final_value": round(portfolio_value, 2),
            "total_return_pct": round(total_return * 100, 2),
            "num_rebalances": sum(1 for p in periods if p["rebalanced"]),
            "total_turnover_pct": round(total_turnover * 100, 2),
            "num_periods": num_periods,
            "periods": periods,
        }

    def compare_strategies(self, num_periods: int = 12, seed: int = 42) -> Dict:
        """Compare rebalanced vs buy-and-hold strategies.

        Args:
            num_periods: Number of periods to simulate.
            seed: Random seed.

        Returns:
            Dict with both strategy results and comparison.
        """
        rebalanced = self.simulate(num_periods=num_periods, rebalance=True, seed=seed)
        buy_hold = self.simulate(num_periods=num_periods, rebalance=False, seed=seed)

        return {
            "rebalanced": {
                "final_value": rebalanced["final_value"],
                "total_return_pct": rebalanced["total_return_pct"],
                "num_rebalances": rebalanced["num_rebalances"],
                "total_turnover_pct": rebalanced["total_turnover_pct"],
            },
            "buy_and_hold": {
                "final_value": buy_hold["final_value"],
                "total_return_pct": buy_hold["total_return_pct"],
            },
            "rebalancing_benefit_pct": round(rebalanced["total_return_pct"] - buy_hold["total_return_pct"], 2),
        }
