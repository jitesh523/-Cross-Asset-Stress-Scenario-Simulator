"""Market regime detector using rolling statistics."""

import logging
from typing import Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class RegimeDetector:
    """Classify market periods into regimes based on rolling returns and volatility."""

    REGIMES = {
        "BULL": "Positive returns, below-average volatility",
        "BEAR": "Negative returns, above-average volatility",
        "CRISIS": "Sharply negative returns, very high volatility",
        "RECOVERY": "Positive returns, elevated volatility",
    }

    def __init__(
        self,
        returns: pd.DataFrame,
        vol_window: int = 21,
        return_window: int = 63,
        crisis_vol_multiplier: float = 2.0,
        crisis_return_threshold: float = -0.15,
    ):
        """Initialize regime detector.

        Args:
            returns: DataFrame with asset return columns.
            vol_window: Rolling window for volatility (default 21 = ~1 month).
            return_window: Rolling window for cumulative returns
                           (default 63 = ~1 quarter).
            crisis_vol_multiplier: How many times above mean vol = crisis.
            crisis_return_threshold: Cumulative return threshold for crisis.
        """
        self.returns = returns
        self.vol_window = vol_window
        self.return_window = return_window
        self.crisis_vol_mult = crisis_vol_multiplier
        self.crisis_return_threshold = crisis_return_threshold

    def detect(self) -> pd.DataFrame:
        """Classify each period into a market regime.

        Returns:
            DataFrame with columns: rolling_vol, rolling_return, regime.
        """
        # Use mean across assets if multiple columns
        if isinstance(self.returns, pd.DataFrame) and len(self.returns.columns) > 1:
            avg_returns = self.returns.mean(axis=1)
        elif isinstance(self.returns, pd.DataFrame):
            avg_returns = self.returns.iloc[:, 0]
        else:
            avg_returns = self.returns

        rolling_vol = avg_returns.rolling(window=self.vol_window).std() * np.sqrt(252)
        rolling_ret = avg_returns.rolling(window=self.return_window).sum()

        result = pd.DataFrame(
            {
                "rolling_vol": rolling_vol,
                "rolling_return": rolling_ret,
            },
            index=avg_returns.index,
        ).dropna()

        mean_vol = result["rolling_vol"].mean()

        regimes = []
        for _, row in result.iterrows():
            vol = row["rolling_vol"]
            ret = row["rolling_return"]

            if (
                ret < self.crisis_return_threshold
                and vol > mean_vol * self.crisis_vol_mult
            ):
                regimes.append("CRISIS")
            elif ret < 0 and vol > mean_vol:
                regimes.append("BEAR")
            elif ret >= 0 and vol > mean_vol:
                regimes.append("RECOVERY")
            else:
                regimes.append("BULL")

        result["regime"] = regimes
        return result

    def summary(self) -> Dict:
        """Generate a summary of regime distribution and statistics.

        Returns:
            Dictionary with regime counts, percentages, and average stats.
        """
        detected = self.detect()
        total = len(detected)

        regime_summary = {}
        for regime in self.REGIMES:
            mask = detected["regime"] == regime
            count = int(mask.sum())
            if count == 0:
                continue
            subset = detected[mask]
            regime_summary[regime] = {
                "count": count,
                "percentage": round(count / total * 100, 1),
                "avg_volatility": round(float(subset["rolling_vol"].mean()), 4),
                "avg_return": round(float(subset["rolling_return"].mean()), 4),
            }

        return {
            "total_periods": total,
            "regimes": regime_summary,
        }
