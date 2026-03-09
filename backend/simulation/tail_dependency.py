"""Tail dependency analyzer.

Measures how assets co-move during extreme events — different
from linear correlation which treats all returns equally.
"""

import logging
from typing import Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TailDependencyAnalyzer:
    """Analyze asset co-movement during extreme market events."""

    def __init__(self, returns: pd.DataFrame, tail_percentile: float = 5.0):
        """Initialize analyzer.

        Args:
            returns: DataFrame with asset return columns.
            tail_percentile: Percentile threshold for tail events (default 5 = bottom/top 5%).
        """
        self.returns = returns
        self.tickers = list(returns.columns)
        self.tail_pct = tail_percentile

    def lower_tail_dependence(self) -> pd.DataFrame:
        """Measure how often assets crash together.

        For each pair, computes the fraction of times asset B is in its
        lower tail given that asset A is in its lower tail.

        Returns:
            DataFrame matrix of lower tail dependence coefficients.
        """
        n = len(self.tickers)
        result = np.eye(n)

        for i in range(n):
            threshold_i = np.percentile(self.returns.iloc[:, i], self.tail_pct)
            tail_mask_i = self.returns.iloc[:, i] <= threshold_i

            for j in range(n):
                if i == j:
                    continue
                threshold_j = np.percentile(self.returns.iloc[:, j], self.tail_pct)
                both_tail = (self.returns.iloc[:, j] <= threshold_j) & tail_mask_i
                count_i = tail_mask_i.sum()
                result[i, j] = float(both_tail.sum() / count_i) if count_i > 0 else 0.0

        return pd.DataFrame(result, index=self.tickers, columns=self.tickers)

    def upper_tail_dependence(self) -> pd.DataFrame:
        """Measure how often assets rally together.

        Returns:
            DataFrame matrix of upper tail dependence coefficients.
        """
        n = len(self.tickers)
        result = np.eye(n)

        for i in range(n):
            threshold_i = np.percentile(self.returns.iloc[:, i], 100 - self.tail_pct)
            tail_mask_i = self.returns.iloc[:, i] >= threshold_i

            for j in range(n):
                if i == j:
                    continue
                threshold_j = np.percentile(self.returns.iloc[:, j], 100 - self.tail_pct)
                both_tail = (self.returns.iloc[:, j] >= threshold_j) & tail_mask_i
                count_i = tail_mask_i.sum()
                result[i, j] = float(both_tail.sum() / count_i) if count_i > 0 else 0.0

        return pd.DataFrame(result, index=self.tickers, columns=self.tickers)

    def crisis_correlation(self, crisis_threshold: float = None) -> pd.DataFrame:
        """Compute correlation using only crisis (tail) observations.

        Args:
            crisis_threshold: Return threshold. Defaults to tail_percentile of avg returns.

        Returns:
            Correlation matrix computed from tail observations only.
        """
        avg = self.returns.mean(axis=1)
        if crisis_threshold is None:
            crisis_threshold = np.percentile(avg, self.tail_pct)

        crisis_mask = avg <= crisis_threshold
        crisis_returns = self.returns[crisis_mask]

        if len(crisis_returns) < 3:
            return self.returns.corr()

        return crisis_returns.corr()

    def compare_normal_vs_crisis(self) -> List[Dict]:
        """Compare correlations during normal vs crisis periods.

        Returns:
            List of dicts showing how each pair's correlation changes.
        """
        normal_corr = self.returns.corr()
        crisis_corr = self.crisis_correlation()

        pairs = []
        for i in range(len(self.tickers)):
            for j in range(i + 1, len(self.tickers)):
                normal = float(normal_corr.iloc[i, j])
                crisis = float(crisis_corr.iloc[i, j])
                pairs.append(
                    {
                        "pair": f"{self.tickers[i]}/{self.tickers[j]}",
                        "normal_correlation": round(normal, 4),
                        "crisis_correlation": round(crisis, 4),
                        "change": round(crisis - normal, 4),
                    }
                )

        pairs.sort(key=lambda x: abs(x["change"]), reverse=True)
        return pairs
