"""Factor exposure analyzer.

Decomposes portfolio returns into systematic factor exposures
(market, size, value) using regression analysis.
"""

import logging
from typing import Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FactorExposureAnalyzer:
    """Decompose returns into factor exposures via regression."""

    def __init__(self, asset_returns: pd.DataFrame, market_returns: pd.Series = None):
        """Initialize analyzer.

        Args:
            asset_returns: DataFrame with asset return columns.
            market_returns: Series of market benchmark returns. If None,
                            uses equal-weighted average of all assets.
        """
        self.returns = asset_returns
        self.tickers = list(asset_returns.columns)

        if market_returns is not None:
            self.market = market_returns
        else:
            self.market = asset_returns.mean(axis=1)

    def compute_beta(self) -> Dict[str, float]:
        """Compute market beta for each asset.

        Beta = Cov(asset, market) / Var(market)

        Returns:
            Dict of ticker → beta value.
        """
        market_var = self.market.var()
        if market_var == 0:
            return {t: 1.0 for t in self.tickers}

        betas = {}
        for ticker in self.tickers:
            cov = self.returns[ticker].cov(self.market)
            betas[ticker] = round(float(cov / market_var), 4)
        return betas

    def compute_alpha(self) -> Dict[str, float]:
        """Compute Jensen's alpha for each asset.

        Alpha = mean(asset_return) - beta * mean(market_return)

        Returns:
            Dict of ticker → annualized alpha.
        """
        betas = self.compute_beta()
        market_mean = self.market.mean()

        alphas = {}
        for ticker in self.tickers:
            asset_mean = self.returns[ticker].mean()
            daily_alpha = asset_mean - betas[ticker] * market_mean
            alphas[ticker] = round(float(daily_alpha * 252), 4)
        return alphas

    def compute_r_squared(self) -> Dict[str, float]:
        """Compute R² (how much of each asset's variance is explained by the market).

        Returns:
            Dict of ticker → R² value (0 to 1).
        """
        r_squared = {}
        for ticker in self.tickers:
            corr = self.returns[ticker].corr(self.market)
            r_squared[ticker] = round(float(corr**2), 4)
        return r_squared

    def compute_tracking_error(self) -> Dict[str, float]:
        """Compute annualized tracking error vs the market.

        Returns:
            Dict of ticker → annualized tracking error.
        """
        errors = {}
        for ticker in self.tickers:
            diff = self.returns[ticker] - self.market
            errors[ticker] = round(float(diff.std() * np.sqrt(252)), 4)
        return errors

    def full_analysis(self) -> Dict:
        """Run full factor exposure analysis.

        Returns:
            Dict with beta, alpha, R², tracking error, and portfolio beta.
        """
        betas = self.compute_beta()
        alphas = self.compute_alpha()
        r_sq = self.compute_r_squared()
        te = self.compute_tracking_error()

        n = len(self.tickers)
        eq_weight = 1.0 / n
        portfolio_beta = sum(b * eq_weight for b in betas.values())

        assets = []
        for ticker in self.tickers:
            assets.append(
                {
                    "ticker": ticker,
                    "beta": betas[ticker],
                    "alpha": alphas[ticker],
                    "r_squared": r_sq[ticker],
                    "tracking_error": te[ticker],
                }
            )

        # Sort by absolute beta (highest systematic risk first)
        assets.sort(key=lambda x: abs(x["beta"]), reverse=True)

        return {
            "portfolio_beta": round(portfolio_beta, 4),
            "assets": assets,
        }
