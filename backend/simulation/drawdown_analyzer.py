"""Drawdown recovery analyzer.

Analyzes drawdown events in detail: duration, depth, time to recovery,
and underwater curves for portfolio stress testing.
"""

import logging
from typing import Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DrawdownAnalyzer:
    """Analyze drawdown events from a price series."""

    def __init__(self, prices: pd.Series, threshold: float = 0.05):
        """Initialize analyzer.

        Args:
            prices: Time series of portfolio prices (indexed by date or int).
            threshold: Minimum drawdown depth to count as an event (e.g. 0.05 = 5%).
        """
        self.prices = prices
        self.threshold = threshold

    def underwater_curve(self) -> pd.Series:
        """Compute the underwater (drawdown) curve.

        Returns:
            Series of drawdown values at each time step (negative decimals).
        """
        cummax = self.prices.cummax()
        return (self.prices - cummax) / cummax

    def find_events(self) -> List[Dict]:
        """Identify distinct drawdown events exceeding the threshold.

        Returns:
            List of drawdown event dicts with peak/trough/recovery info.
        """
        underwater = self.underwater_curve()
        events = []
        in_drawdown = False
        peak_idx = None
        trough_idx = None
        trough_val = 0.0

        for i in range(len(underwater)):
            dd = underwater.iloc[i]

            if not in_drawdown and dd < -self.threshold:
                in_drawdown = True
                # Peak is the last point before drawdown started
                peak_idx = i - 1 if i > 0 else 0
                trough_idx = i
                trough_val = dd

            elif in_drawdown:
                if dd < trough_val:
                    trough_idx = i
                    trough_val = dd

                if dd >= 0:
                    # Recovery complete
                    events.append(self._build_event(peak_idx, trough_idx, i, trough_val))
                    in_drawdown = False
                    trough_val = 0.0

        # Handle ongoing drawdown (no recovery yet)
        if in_drawdown:
            events.append(self._build_event(peak_idx, trough_idx, len(underwater) - 1, trough_val, recovered=False))

        return events

    def _build_event(self, peak_idx, trough_idx, end_idx, depth, recovered=True) -> Dict:
        """Build a drawdown event dict."""
        idx = self.prices.index
        return {
            "peak_date": str(idx[peak_idx]),
            "trough_date": str(idx[trough_idx]),
            "recovery_date": str(idx[end_idx]) if recovered else None,
            "depth": round(float(depth), 4),
            "duration_to_trough": trough_idx - peak_idx,
            "duration_to_recovery": (end_idx - peak_idx) if recovered else None,
            "recovered": recovered,
        }

    def summary(self) -> Dict:
        """Generate a summary of all drawdown events.

        Returns:
            Dict with stats about drawdown history.
        """
        events = self.find_events()
        if not events:
            return {
                "num_events": 0,
                "max_drawdown": 0.0,
                "avg_drawdown": 0.0,
                "avg_recovery_days": 0,
                "longest_recovery_days": 0,
                "events": [],
            }

        depths = [abs(e["depth"]) for e in events]
        recovery_durations = [e["duration_to_recovery"] for e in events if e["recovered"] and e["duration_to_recovery"]]

        return {
            "num_events": len(events),
            "max_drawdown": round(max(depths), 4),
            "avg_drawdown": round(float(np.mean(depths)), 4),
            "avg_recovery_days": int(np.mean(recovery_durations)) if recovery_durations else None,
            "longest_recovery_days": max(recovery_durations) if recovery_durations else None,
            "events": events,
        }
