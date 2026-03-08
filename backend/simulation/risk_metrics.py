"""Advanced risk metrics for portfolio analysis."""

import logging

import numpy as np

logger = logging.getLogger(__name__)


class RiskMetrics:
    """Compute advanced risk metrics from simulation results."""

    @staticmethod
    def max_drawdown(prices: np.ndarray) -> float:
        """Calculate maximum drawdown from a price series.

        Args:
            prices: 1-D array of portfolio prices over time.

        Returns:
            Maximum drawdown as a negative decimal (e.g. -0.25 for 25% loss).
        """
        cumulative_max = np.maximum.accumulate(prices)
        drawdowns = (prices - cumulative_max) / cumulative_max
        return float(np.min(drawdowns))

    @staticmethod
    def sortino_ratio(
        returns: np.ndarray,
        target_return: float = 0.0,
        annualization_factor: float = 252.0,
    ) -> float:
        """Calculate Sortino ratio (return per unit of downside risk).

        Args:
            returns: Array of periodic returns.
            target_return: Minimum acceptable return per period.
            annualization_factor: Trading days per year.

        Returns:
            Annualized Sortino ratio.
        """
        excess = returns - target_return
        downside = excess[excess < 0]

        if len(downside) == 0:
            return float("inf")

        downside_std = np.sqrt(np.mean(downside**2))
        if downside_std == 0:
            return float("inf")

        mean_excess = np.mean(excess)
        return float(mean_excess / downside_std * np.sqrt(annualization_factor))

    @staticmethod
    def calmar_ratio(returns: np.ndarray, prices: np.ndarray, annualization_factor: float = 252.0) -> float:
        """Calculate Calmar ratio (annualized return / max drawdown).

        Args:
            returns: Array of periodic returns.
            prices: Array of prices.
            annualization_factor: Trading days per year.

        Returns:
            Calmar ratio (positive means good risk-adjusted return).
        """
        mdd = RiskMetrics.max_drawdown(prices)
        if mdd == 0:
            return float("inf")

        annualized_return = np.mean(returns) * annualization_factor
        return float(-annualized_return / mdd)

    @staticmethod
    def omega_ratio(returns: np.ndarray, threshold: float = 0.0) -> float:
        """Calculate Omega ratio (probability-weighted gains vs losses).

        Args:
            returns: Array of periodic returns.
            threshold: Return threshold separating gains from losses.

        Returns:
            Omega ratio. Values > 1 indicate favourable risk/reward.
        """
        gains = returns[returns > threshold] - threshold
        losses = threshold - returns[returns <= threshold]

        sum_losses = np.sum(losses)
        if sum_losses == 0:
            return float("inf")

        return float(np.sum(gains) / sum_losses)

    @staticmethod
    def tail_risk_index(returns: np.ndarray, confidence: float = 0.95) -> float:
        """Calculate tail risk index (CVaR / VaR ratio).

        Measures how heavy the tail is. Values much greater than 1
        indicate fat tails with concentrated extreme losses.

        Args:
            returns: Array of periodic returns.
            confidence: Confidence level for VaR/CVaR.

        Returns:
            Tail risk index.
        """
        var = np.percentile(returns, (1 - confidence) * 100)
        if var == 0:
            return 1.0

        tail_losses = returns[returns <= var]
        if len(tail_losses) == 0:
            return 1.0

        cvar = np.mean(tail_losses)
        return float(cvar / var)

    @staticmethod
    def compute_all(
        prices: np.ndarray,
        returns: np.ndarray,
        confidence: float = 0.95,
    ) -> dict:
        """Compute all risk metrics at once.

        Args:
            prices: 1-D array of portfolio prices.
            returns: 1-D array of periodic returns.
            confidence: Confidence level for tail risk.

        Returns:
            Dictionary with all computed metrics.
        """
        return {
            "max_drawdown": RiskMetrics.max_drawdown(prices),
            "sortino_ratio": RiskMetrics.sortino_ratio(returns),
            "calmar_ratio": RiskMetrics.calmar_ratio(returns, prices),
            "omega_ratio": RiskMetrics.omega_ratio(returns),
            "tail_risk_index": RiskMetrics.tail_risk_index(returns, confidence),
        }
