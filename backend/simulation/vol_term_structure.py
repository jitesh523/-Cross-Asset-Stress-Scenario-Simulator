"""Volatility term structure analyzer.

Computes and compares volatility at different time horizons
to reveal how risk scales over time.
"""

import logging
from typing import Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class VolatilityTermStructure:
    """Analyze how volatility changes across time horizons."""

    DEFAULT_WINDOWS = [5, 10, 21, 63, 126, 252]

    def __init__(self, returns: pd.DataFrame):
        """Initialize with asset returns.

        Args:
            returns: DataFrame of daily returns with tickers as columns.
        """
        self.returns = returns
        self.tickers = list(returns.columns)

    def rolling_volatility(self, window: int = 21) -> pd.DataFrame:
        """Compute rolling annualized volatility.

        Args:
            window: Rolling window size in trading days.

        Returns:
            DataFrame of rolling volatilities.
        """
        return self.returns.rolling(window=window).std() * np.sqrt(252)

    def term_structure(self, windows: List[int] = None) -> Dict:
        """Compute annualized volatility at multiple time horizons.

        Args:
            windows: List of lookback windows (trading days).

        Returns:
            Dict with per-asset volatility at each horizon.
        """
        if windows is None:
            windows = self.DEFAULT_WINDOWS

        # Filter valid windows
        windows = [w for w in windows if w <= len(self.returns)]

        result = {}
        for ticker in self.tickers:
            vols = {}
            for w in windows:
                recent = self.returns[ticker].iloc[-w:]
                vols[f"{w}d"] = round(float(recent.std() * np.sqrt(252)), 4)
            result[ticker] = vols

        return result

    def volatility_cone(self, windows: List[int] = None, percentiles: List[int] = None) -> Dict:
        """Build a volatility cone showing historical vol distribution.

        For each window, computes percentile bands from rolling vol history.

        Args:
            windows: Lookback windows.
            percentiles: Percentiles to compute (e.g. [10, 25, 50, 75, 90]).

        Returns:
            Dict with cone data per ticker.
        """
        if windows is None:
            windows = [w for w in self.DEFAULT_WINDOWS if w <= len(self.returns)]
        if percentiles is None:
            percentiles = [10, 25, 50, 75, 90]

        cone = {}
        for ticker in self.tickers:
            bands = {}
            for w in windows:
                rolling_vol = self.returns[ticker].rolling(w).std() * np.sqrt(252)
                rolling_vol = rolling_vol.dropna()
                if len(rolling_vol) == 0:
                    continue
                bands[f"{w}d"] = {f"p{p}": round(float(np.percentile(rolling_vol, p)), 4) for p in percentiles}
                bands[f"{w}d"]["current"] = round(float(rolling_vol.iloc[-1]), 4)
            cone[ticker] = bands

        return cone

    def is_elevated(self, threshold_percentile: float = 75) -> Dict[str, bool]:
        """Check if current volatility is elevated vs history.

        Args:
            threshold_percentile: Percentile above which vol is "elevated".

        Returns:
            Dict of ticker → bool.
        """
        result = {}
        for ticker in self.tickers:
            rolling = self.returns[ticker].rolling(21).std() * np.sqrt(252)
            rolling = rolling.dropna()
            if len(rolling) == 0:
                result[ticker] = False
                continue
            current = rolling.iloc[-1]
            threshold = np.percentile(rolling, threshold_percentile)
            result[ticker] = bool(current > threshold)
        return result
