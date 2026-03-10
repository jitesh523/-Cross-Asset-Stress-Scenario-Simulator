"""Position sizing using Kelly criterion.

Computes optimal bet sizes based on expected return and risk,
with fractional Kelly for more conservative sizing.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class PositionSizer:
    """Calculate optimal position sizes using Kelly criterion."""

    def __init__(
        self,
        expected_returns: Dict[str, float],
        volatilities: Dict[str, float],
        risk_free_rate: float = 0.04,
    ):
        """Initialize sizer.

        Args:
            expected_returns: Dict of ticker → annualized expected return.
            volatilities: Dict of ticker → annualized volatility.
            risk_free_rate: Annual risk-free rate.
        """
        self.tickers = sorted(expected_returns.keys())
        self.returns = expected_returns
        self.vols = volatilities
        self.rf = risk_free_rate

    def kelly_fraction(self, ticker: str) -> float:
        """Compute full Kelly fraction for a single asset.

        Kelly f* = (mu - rf) / sigma^2

        Args:
            ticker: Asset ticker.

        Returns:
            Optimal fraction of capital to allocate.
        """
        mu = self.returns[ticker]
        sigma = self.vols[ticker]
        if sigma == 0:
            return 0.0
        return float((mu - self.rf) / (sigma**2))

    def fractional_kelly(self, ticker: str, fraction: float = 0.5) -> float:
        """Compute fractional Kelly (more conservative).

        Args:
            ticker: Asset ticker.
            fraction: Kelly fraction (0.5 = half-Kelly, commonly used in practice).

        Returns:
            Scaled position size.
        """
        return self.kelly_fraction(ticker) * fraction

    def optimal_sizes(self, kelly_fraction: float = 0.5, max_position: float = 0.40) -> List[Dict]:
        """Compute optimal position sizes for all assets.

        Args:
            kelly_fraction: Kelly scaling factor (1.0 = full, 0.5 = half).
            max_position: Maximum allowed position size per asset.

        Returns:
            List of position sizing recommendations.
        """
        results = []
        for ticker in self.tickers:
            full_kelly = self.kelly_fraction(ticker)
            sized = full_kelly * kelly_fraction
            capped = max(min(sized, max_position), -max_position)

            excess_return = self.returns[ticker] - self.rf
            sharpe = excess_return / self.vols[ticker] if self.vols[ticker] > 0 else 0.0

            results.append(
                {
                    "ticker": ticker,
                    "expected_return": round(self.returns[ticker], 4),
                    "volatility": round(self.vols[ticker], 4),
                    "sharpe_ratio": round(sharpe, 4),
                    "full_kelly": round(full_kelly, 4),
                    "sized_position": round(sized, 4),
                    "capped_position": round(capped, 4),
                    "signal": "OVERWEIGHT" if capped > 0.05 else ("UNDERWEIGHT" if capped < -0.05 else "NEUTRAL"),
                }
            )

        results.sort(key=lambda x: x["sharpe_ratio"], reverse=True)
        return results

    def portfolio_summary(self, kelly_fraction: float = 0.5, max_position: float = 0.40) -> Dict:
        """Full portfolio sizing summary.

        Args:
            kelly_fraction: Kelly scaling factor.
            max_position: Max position per asset.

        Returns:
            Dict with positions, cash allocation, and leverage stats.
        """
        positions = self.optimal_sizes(kelly_fraction, max_position)
        total_allocated = sum(abs(p["capped_position"]) for p in positions)
        long_exposure = sum(p["capped_position"] for p in positions if p["capped_position"] > 0)
        short_exposure = sum(abs(p["capped_position"]) for p in positions if p["capped_position"] < 0)

        return {
            "kelly_fraction": kelly_fraction,
            "max_position": max_position,
            "positions": positions,
            "total_allocated": round(total_allocated, 4),
            "cash_reserve": round(max(0, 1.0 - total_allocated), 4),
            "long_exposure": round(long_exposure, 4),
            "short_exposure": round(short_exposure, 4),
            "gross_exposure": round(total_allocated, 4),
            "net_exposure": round(long_exposure - short_exposure, 4),
        }
