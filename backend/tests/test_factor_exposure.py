"""Tests for factor exposure analyzer."""

import numpy as np
import pandas as pd

from backend.simulation.factor_exposure import FactorExposureAnalyzer


def _make_returns(n=252, seed=42):
    """Create multi-asset returns with known factor structure."""
    np.random.seed(seed)
    market = np.random.normal(0.0004, 0.01, n)
    # SPY tracks market closely (high beta)
    spy = market * 1.1 + np.random.normal(0, 0.003, n)
    # TLT has low/negative beta to equity market
    tlt = market * -0.2 + np.random.normal(0.0001, 0.005, n)
    # GLD is somewhat independent
    gld = market * 0.3 + np.random.normal(0.0002, 0.006, n)

    dates = pd.date_range("2023-01-01", periods=n, freq="B")
    asset_df = pd.DataFrame({"SPY": spy, "TLT": tlt, "GLD": gld}, index=dates)
    market_series = pd.Series(market, index=dates, name="Market")
    return asset_df, market_series


class TestBeta:
    def test_returns_all_tickers(self):
        assets, market = _make_returns()
        betas = FactorExposureAnalyzer(assets, market).compute_beta()
        assert set(betas.keys()) == {"SPY", "TLT", "GLD"}

    def test_spy_high_beta(self):
        """SPY was constructed with beta ~1.1."""
        assets, market = _make_returns()
        betas = FactorExposureAnalyzer(assets, market).compute_beta()
        assert betas["SPY"] > 0.8

    def test_tlt_negative_beta(self):
        """TLT was constructed with negative beta."""
        assets, market = _make_returns()
        betas = FactorExposureAnalyzer(assets, market).compute_beta()
        assert betas["TLT"] < 0


class TestAlpha:
    def test_returns_all_tickers(self):
        assets, market = _make_returns()
        alphas = FactorExposureAnalyzer(assets, market).compute_alpha()
        assert set(alphas.keys()) == {"SPY", "TLT", "GLD"}

    def test_alpha_is_float(self):
        assets, market = _make_returns()
        alphas = FactorExposureAnalyzer(assets, market).compute_alpha()
        for v in alphas.values():
            assert isinstance(v, float)


class TestRSquared:
    def test_between_zero_and_one(self):
        assets, market = _make_returns()
        r2 = FactorExposureAnalyzer(assets, market).compute_r_squared()
        for v in r2.values():
            assert 0 <= v <= 1

    def test_spy_high_r_squared(self):
        """SPY closely tracks market, R² should be high."""
        assets, market = _make_returns()
        r2 = FactorExposureAnalyzer(assets, market).compute_r_squared()
        assert r2["SPY"] > 0.5


class TestTrackingError:
    def test_all_positive(self):
        assets, market = _make_returns()
        te = FactorExposureAnalyzer(assets, market).compute_tracking_error()
        for v in te.values():
            assert v > 0


class TestFullAnalysis:
    def test_has_portfolio_beta(self):
        assets, market = _make_returns()
        result = FactorExposureAnalyzer(assets, market).full_analysis()
        assert "portfolio_beta" in result

    def test_has_assets(self):
        assets, market = _make_returns()
        result = FactorExposureAnalyzer(assets, market).full_analysis()
        assert len(result["assets"]) == 3

    def test_asset_has_all_fields(self):
        assets, market = _make_returns()
        result = FactorExposureAnalyzer(assets, market).full_analysis()
        asset = result["assets"][0]
        expected = {"ticker", "beta", "alpha", "r_squared", "tracking_error"}
        assert expected.issubset(set(asset.keys()))

    def test_sorted_by_beta(self):
        assets, market = _make_returns()
        result = FactorExposureAnalyzer(assets, market).full_analysis()
        betas = [abs(a["beta"]) for a in result["assets"]]
        assert betas == sorted(betas, reverse=True)

    def test_no_market_arg(self):
        """Should work without explicit market returns."""
        assets, _ = _make_returns()
        result = FactorExposureAnalyzer(assets).full_analysis()
        assert "portfolio_beta" in result
