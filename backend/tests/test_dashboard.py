"""Tests for dashboard aggregator."""

import numpy as np
import pandas as pd

from backend.simulation.dashboard import DashboardAggregator


def _make_dashboard():
    np.random.seed(42)
    n = 252
    dates = pd.date_range("2023-01-01", periods=n, freq="B")
    returns = pd.DataFrame(
        {
            "SPY": np.random.normal(0.0004, 0.012, n),
            "TLT": np.random.normal(0.0001, 0.007, n),
            "GLD": np.random.normal(0.0003, 0.010, n),
        },
        index=dates,
    )
    weights = {"SPY": 0.50, "TLT": 0.30, "GLD": 0.20}
    return DashboardAggregator(returns, weights)


class TestSummaryStats:
    def test_has_required_keys(self):
        result = _make_dashboard().summary_stats()
        required = {"annualized_return", "annualized_volatility", "sharpe_ratio", "daily_var_95"}
        assert required.issubset(set(result.keys()))

    def test_vol_positive(self):
        result = _make_dashboard().summary_stats()
        assert result["annualized_volatility"] > 0


class TestPerAssetStats:
    def test_returns_all_assets(self):
        result = _make_dashboard().per_asset_stats()
        assert len(result) == 3

    def test_sorted_by_sharpe(self):
        result = _make_dashboard().per_asset_stats()
        sharpes = [a["sharpe_ratio"] for a in result]
        assert sharpes == sorted(sharpes, reverse=True)

    def test_has_weight(self):
        result = _make_dashboard().per_asset_stats()
        for asset in result:
            assert "weight" in asset


class TestRiskMetrics:
    def test_returns_all_metrics(self):
        result = _make_dashboard().risk_metrics_summary()
        assert "max_drawdown" in result
        assert "sortino_ratio" in result


class TestVolStructure:
    def test_returns_all_tickers(self):
        result = _make_dashboard().vol_structure()
        assert "SPY" in result
        assert "TLT" in result


class TestGenerate:
    def test_has_all_sections(self):
        result = _make_dashboard().generate()
        assert "portfolio_summary" in result
        assert "risk_metrics" in result
        assert "per_asset" in result
        assert "vol_term_structure" in result

    def test_portfolio_summary_is_dict(self):
        result = _make_dashboard().generate()
        assert isinstance(result["portfolio_summary"], dict)

    def test_per_asset_is_list(self):
        result = _make_dashboard().generate()
        assert isinstance(result["per_asset"], list)
