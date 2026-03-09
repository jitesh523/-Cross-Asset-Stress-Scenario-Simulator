"""Tests for tail dependency analyzer."""

import numpy as np
import pandas as pd

from backend.simulation.tail_dependency import TailDependencyAnalyzer


def _make_returns(n=500, seed=42):
    """Create correlated returns with fat tails."""
    np.random.seed(seed)
    # Create correlated returns
    cov = [[0.0001, 0.00005, 0.00002], [0.00005, 0.0001, 0.00003], [0.00002, 0.00003, 0.00008]]
    returns = np.random.multivariate_normal([0.0003, 0.0001, 0.0002], cov, n)
    dates = pd.date_range("2022-01-01", periods=n, freq="B")
    return pd.DataFrame(returns, index=dates, columns=["SPY", "TLT", "GLD"])


class TestLowerTailDependence:
    def test_returns_matrix(self):
        df = _make_returns()
        result = TailDependencyAnalyzer(df).lower_tail_dependence()
        assert result.shape == (3, 3)

    def test_diagonal_is_one(self):
        df = _make_returns()
        result = TailDependencyAnalyzer(df).lower_tail_dependence()
        np.testing.assert_array_almost_equal(np.diag(result.values), 1.0)

    def test_values_between_zero_and_one(self):
        df = _make_returns()
        result = TailDependencyAnalyzer(df).lower_tail_dependence()
        assert (result.values >= 0).all()
        assert (result.values <= 1).all()


class TestUpperTailDependence:
    def test_returns_matrix(self):
        df = _make_returns()
        result = TailDependencyAnalyzer(df).upper_tail_dependence()
        assert result.shape == (3, 3)

    def test_diagonal_is_one(self):
        df = _make_returns()
        result = TailDependencyAnalyzer(df).upper_tail_dependence()
        np.testing.assert_array_almost_equal(np.diag(result.values), 1.0)


class TestCrisisCorrelation:
    def test_returns_matrix(self):
        df = _make_returns()
        result = TailDependencyAnalyzer(df).crisis_correlation()
        assert result.shape == (3, 3)

    def test_diagonal_is_one(self):
        df = _make_returns()
        result = TailDependencyAnalyzer(df).crisis_correlation()
        np.testing.assert_array_almost_equal(np.diag(result.values), 1.0)


class TestNormalVsCrisis:
    def test_returns_pairs(self):
        df = _make_returns()
        result = TailDependencyAnalyzer(df).compare_normal_vs_crisis()
        assert len(result) == 3  # 3 pairs from 3 assets

    def test_has_required_fields(self):
        df = _make_returns()
        pair = TailDependencyAnalyzer(df).compare_normal_vs_crisis()[0]
        assert "pair" in pair
        assert "normal_correlation" in pair
        assert "crisis_correlation" in pair
        assert "change" in pair

    def test_sorted_by_change(self):
        df = _make_returns()
        result = TailDependencyAnalyzer(df).compare_normal_vs_crisis()
        changes = [abs(p["change"]) for p in result]
        assert changes == sorted(changes, reverse=True)
