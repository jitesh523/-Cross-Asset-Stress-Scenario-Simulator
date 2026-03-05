"""Tests for risk metrics module."""

import numpy as np

from backend.simulation.risk_metrics import RiskMetrics


class TestMaxDrawdown:
    """Tests for max drawdown calculation."""

    def test_no_drawdown(self):
        """Monotonically increasing prices have zero drawdown."""
        prices = np.array([100, 110, 120, 130, 140])
        assert RiskMetrics.max_drawdown(prices) == 0.0

    def test_simple_drawdown(self):
        """Price drops from 200 to 100 = -50% drawdown."""
        prices = np.array([100, 200, 100, 150])
        assert abs(RiskMetrics.max_drawdown(prices) - (-0.5)) < 1e-10

    def test_drawdown_at_end(self):
        """Drawdown that hasn't recovered."""
        prices = np.array([100, 120, 80])
        expected = (80 - 120) / 120  # -0.3333
        assert abs(RiskMetrics.max_drawdown(prices) - expected) < 1e-4


class TestSortinoRatio:
    """Tests for Sortino ratio."""

    def test_all_positive_returns(self):
        """No downside → infinite Sortino."""
        returns = np.array([0.01, 0.02, 0.03, 0.01])
        assert RiskMetrics.sortino_ratio(returns) == float("inf")

    def test_mixed_returns(self):
        """Mixed returns produce a finite ratio."""
        returns = np.array([0.02, -0.01, 0.03, -0.02, 0.01])
        ratio = RiskMetrics.sortino_ratio(returns)
        assert np.isfinite(ratio)

    def test_negative_returns_negative_ratio(self):
        """Mostly negative returns produce a negative Sortino."""
        returns = np.array([-0.05, -0.03, -0.04, 0.01, -0.02])
        ratio = RiskMetrics.sortino_ratio(returns)
        assert ratio < 0


class TestCalmarRatio:
    """Tests for Calmar ratio."""

    def test_positive_calmar(self):
        """Positive returns with drawdown give a positive Calmar."""
        prices = np.array([100, 110, 90, 105, 115])
        returns = np.diff(prices) / prices[:-1]
        ratio = RiskMetrics.calmar_ratio(returns, prices)
        assert ratio > 0

    def test_no_drawdown_infinite(self):
        """No drawdown → infinite Calmar."""
        prices = np.array([100, 110, 120, 130])
        returns = np.diff(prices) / prices[:-1]
        assert RiskMetrics.calmar_ratio(returns, prices) == float("inf")


class TestOmegaRatio:
    """Tests for Omega ratio."""

    def test_all_gains(self):
        """All positive returns → infinite Omega."""
        returns = np.array([0.01, 0.02, 0.03])
        assert RiskMetrics.omega_ratio(returns) == float("inf")

    def test_equal_gains_losses(self):
        """Symmetric returns around zero ≈ Omega of 1."""
        returns = np.array([0.01, -0.01, 0.02, -0.02])
        ratio = RiskMetrics.omega_ratio(returns)
        assert abs(ratio - 1.0) < 0.01

    def test_mostly_losses(self):
        """Mostly losses → Omega < 1."""
        returns = np.array([-0.05, -0.03, 0.01, -0.04])
        ratio = RiskMetrics.omega_ratio(returns)
        assert ratio < 1.0


class TestTailRiskIndex:
    """Tests for tail risk index."""

    def test_normal_distribution(self):
        """Normal distribution tail risk index should be close to 1."""
        np.random.seed(42)
        returns = np.random.normal(0, 0.01, 10000)
        tri = RiskMetrics.tail_risk_index(returns)
        # For normal distribution, CVaR/VaR ≈ 1.15-1.25
        assert 1.0 <= tri <= 1.5

    def test_always_positive(self):
        """Tail risk index should always be positive."""
        returns = np.array([-0.05, -0.03, -0.01, 0.01, 0.02, 0.03])
        tri = RiskMetrics.tail_risk_index(returns)
        assert tri > 0


class TestComputeAll:
    """Tests for the convenience method."""

    def test_returns_all_keys(self):
        """compute_all returns all expected metric keys."""
        prices = np.array([100, 110, 105, 115, 108])
        returns = np.diff(prices) / prices[:-1]
        result = RiskMetrics.compute_all(prices, returns)

        expected_keys = {
            "max_drawdown",
            "sortino_ratio",
            "calmar_ratio",
            "omega_ratio",
            "tail_risk_index",
        }
        assert set(result.keys()) == expected_keys

    def test_all_values_are_floats(self):
        """All metrics should be float values."""
        prices = np.array([100, 110, 105, 115, 108])
        returns = np.diff(prices) / prices[:-1]
        result = RiskMetrics.compute_all(prices, returns)

        for value in result.values():
            assert isinstance(value, float)
