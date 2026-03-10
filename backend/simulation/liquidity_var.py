"""Liquidity-adjusted VaR.

Extends standard VaR by incorporating bid-ask spread costs
and market impact from position liquidation.
"""

import logging
from typing import Dict, List

import numpy as np

logger = logging.getLogger(__name__)


class LiquidityAdjustedVaR:
    """Compute VaR adjusted for liquidity costs."""

    def __init__(
        self,
        tickers: List[str],
        portfolio_values: Dict[str, float],
        daily_volumes: Dict[str, float],
        bid_ask_spreads: Dict[str, float],
        volatilities: Dict[str, float],
    ):
        """Initialize LVaR calculator.

        Args:
            tickers: Asset ticker symbols.
            portfolio_values: Dict of ticker → position value in dollars.
            daily_volumes: Dict of ticker → average daily trading volume in dollars.
            bid_ask_spreads: Dict of ticker → bid-ask spread as fraction (e.g. 0.001 = 10bps).
            volatilities: Dict of ticker → daily volatility (not annualized).
        """
        self.tickers = tickers
        self.values = portfolio_values
        self.volumes = daily_volumes
        self.spreads = bid_ask_spreads
        self.vols = volatilities

    def spread_cost(self, ticker: str) -> float:
        """Half-spread cost for liquidating a position.

        Returns:
            Dollar cost of crossing the spread.
        """
        return self.values[ticker] * self.spreads[ticker] / 2.0

    def market_impact(self, ticker: str, participation_rate: float = 0.10) -> float:
        """Estimate market impact cost using square-root model.

        Impact = sigma * sqrt(position_value / (participation_rate * daily_volume))

        Args:
            ticker: Asset ticker.
            participation_rate: Fraction of daily volume willing to trade.

        Returns:
            Estimated market impact as dollar cost.
        """
        pos = self.values[ticker]
        vol = self.vols[ticker]
        adv = self.volumes[ticker]

        if adv <= 0 or participation_rate <= 0:
            return 0.0

        days_to_liquidate = pos / (participation_rate * adv)
        impact_pct = vol * np.sqrt(max(days_to_liquidate, 0))
        return float(pos * impact_pct)

    def liquidity_cost(self, ticker: str) -> float:
        """Total liquidity cost = spread + market impact."""
        return self.spread_cost(ticker) + self.market_impact(ticker)

    def standard_var(self, confidence: float = 0.95) -> float:
        """Compute standard parametric portfolio VaR (no liquidity adjustment).

        Args:
            confidence: VaR confidence level.

        Returns:
            Portfolio VaR as a positive dollar amount.
        """
        z = {0.90: 1.282, 0.95: 1.645, 0.99: 2.326}.get(confidence, 1.645)

        total_value = sum(self.values.values())
        if total_value == 0:
            return 0.0

        # Weight-adjusted portfolio volatility (uncorrelated approximation)
        weighted_var = 0.0
        for t in self.tickers:
            w = self.values[t] / total_value
            weighted_var += (w * self.vols[t]) ** 2
        port_vol = np.sqrt(weighted_var)

        return float(z * port_vol * total_value)

    def adjusted_var(self, confidence: float = 0.95) -> float:
        """Compute liquidity-adjusted VaR.

        LVaR = standard_VaR + total_liquidity_cost

        Args:
            confidence: VaR confidence level.

        Returns:
            Liquidity-adjusted VaR as a positive dollar amount.
        """
        base = self.standard_var(confidence)
        liq_cost = sum(self.liquidity_cost(t) for t in self.tickers)
        return float(base + liq_cost)

    def decomposition(self, confidence: float = 0.95) -> Dict:
        """Full liquidity VaR decomposition.

        Returns:
            Dict with standard VaR, liquidity costs, adjusted VaR, and per-asset detail.
        """
        std_var = self.standard_var(confidence)
        total_value = sum(self.values.values())

        assets = []
        total_spread = 0.0
        total_impact = 0.0

        for t in self.tickers:
            sc = self.spread_cost(t)
            mi = self.market_impact(t)
            total_spread += sc
            total_impact += mi

            days = self.values[t] / (0.10 * self.volumes[t]) if self.volumes[t] > 0 else float("inf")

            assets.append(
                {
                    "ticker": t,
                    "position_value": round(self.values[t], 2),
                    "spread_cost": round(sc, 2),
                    "market_impact": round(mi, 2),
                    "total_liquidity_cost": round(sc + mi, 2),
                    "days_to_liquidate": round(days, 1),
                    "liquidity_grade": self._grade_liquidity(days),
                }
            )

        assets.sort(key=lambda x: x["total_liquidity_cost"], reverse=True)

        return {
            "portfolio_value": round(total_value, 2),
            "standard_var": round(std_var, 2),
            "spread_cost_total": round(total_spread, 2),
            "impact_cost_total": round(total_impact, 2),
            "liquidity_adjusted_var": round(std_var + total_spread + total_impact, 2),
            "liquidity_premium_pct": round((total_spread + total_impact) / std_var * 100 if std_var > 0 else 0, 1),
            "assets": assets,
        }

    @staticmethod
    def _grade_liquidity(days_to_liquidate: float) -> str:
        """Grade asset liquidity based on liquidation time."""
        if days_to_liquidate <= 0.5:
            return "EXCELLENT"
        elif days_to_liquidate <= 2:
            return "GOOD"
        elif days_to_liquidate <= 5:
            return "MODERATE"
        elif days_to_liquidate <= 20:
            return "POOR"
        return "ILLIQUID"
