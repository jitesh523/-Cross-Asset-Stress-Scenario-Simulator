"""Backtesting engine for validating scenario predictions."""

import logging
from typing import Dict

import numpy as np

logger = logging.getLogger(__name__)


class Backtester:
    """Validate stress scenario predictions against actual historical outcomes."""

    def __init__(
        self,
        predicted_returns: Dict[str, float],
        actual_returns: Dict[str, float],
    ):
        """Initialize backtester.

        Args:
            predicted_returns: Dict of ticker → predicted return (decimal).
            actual_returns: Dict of ticker → actual historical return (decimal).
        """
        # Match only tickers present in both
        common = sorted(set(predicted_returns.keys()) & set(actual_returns.keys()))
        self.tickers = common
        self.predicted = np.array([predicted_returns[t] for t in common])
        self.actual = np.array([actual_returns[t] for t in common])

    def rmse(self) -> float:
        """Root Mean Squared Error between predicted and actual returns.

        Returns:
            RMSE value.
        """
        if len(self.tickers) == 0:
            return 0.0
        return float(np.sqrt(np.mean((self.predicted - self.actual) ** 2)))

    def mae(self) -> float:
        """Mean Absolute Error between predicted and actual returns.

        Returns:
            MAE value.
        """
        if len(self.tickers) == 0:
            return 0.0
        return float(np.mean(np.abs(self.predicted - self.actual)))

    def direction_accuracy(self) -> float:
        """Fraction of assets where the predicted direction was correct.

        Direction = sign of return (positive vs negative).

        Returns:
            Accuracy between 0.0 and 1.0.
        """
        if len(self.tickers) == 0:
            return 0.0

        pred_sign = np.sign(self.predicted)
        actual_sign = np.sign(self.actual)
        return float(np.mean(pred_sign == actual_sign))

    def severity_accuracy(self) -> float:
        """How close predicted magnitudes are to actual magnitudes.

        Uses 1 - normalized MAE (capped at 0). A value of 1.0 means
        perfect magnitude prediction.

        Returns:
            Severity accuracy between 0.0 and 1.0.
        """
        if len(self.tickers) == 0:
            return 0.0

        actual_range = np.max(np.abs(self.actual))
        if actual_range == 0:
            return 1.0 if self.mae() == 0 else 0.0

        normalized_mae = self.mae() / actual_range
        return float(max(0.0, 1.0 - normalized_mae))

    def per_asset_comparison(self) -> list:
        """Detailed per-asset comparison of predicted vs actual.

        Returns:
            List of per-asset comparison dicts.
        """
        results = []
        for i, ticker in enumerate(self.tickers):
            pred = float(self.predicted[i])
            actual = float(self.actual[i])
            error = pred - actual
            direction_match = np.sign(pred) == np.sign(actual)

            results.append(
                {
                    "ticker": ticker,
                    "predicted_return": round(pred, 4),
                    "actual_return": round(actual, 4),
                    "error": round(error, 4),
                    "abs_error": round(abs(error), 4),
                    "direction_correct": bool(direction_match),
                }
            )

        results.sort(key=lambda x: x["abs_error"], reverse=True)
        return results

    def backtest(self) -> Dict:
        """Run full backtest and return structured results.

        Returns:
            Dictionary with all backtesting metrics.
        """
        comparison = self.per_asset_comparison()
        correct_count = sum(1 for a in comparison if a["direction_correct"])

        return {
            "num_assets": len(self.tickers),
            "rmse": round(self.rmse(), 6),
            "mae": round(self.mae(), 6),
            "direction_accuracy": round(self.direction_accuracy(), 4),
            "severity_accuracy": round(self.severity_accuracy(), 4),
            "correct_direction_count": correct_count,
            "per_asset": comparison,
            "overall_grade": self._grade(),
        }

    def _grade(self) -> str:
        """Assign a letter grade based on combined accuracy."""
        dir_acc = self.direction_accuracy()
        sev_acc = self.severity_accuracy()
        combined = dir_acc * 0.6 + sev_acc * 0.4

        if combined >= 0.85:
            return "A"
        elif combined >= 0.70:
            return "B"
        elif combined >= 0.55:
            return "C"
        elif combined >= 0.40:
            return "D"
        return "F"
