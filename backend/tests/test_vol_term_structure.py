"""Tests for volatility term structure analyzer."""

import numpy as np
import pandas as pd

from backend.simulation.vol_term_structure import VolatilityTermStructure


def _make_returns(n=300, seed=42):
    np.random.seed(seed)
    dates = pd.date_range("2022-01-01", periods=n, freq="B")
    return pd.DataFrame(
        {"SPY": np.random.normal(0.0004, 0.012, n), "TLT": np.random.normal(0.0001, 0.008, n)},
        index=dates,
    )


class TestRollingVolatility:
    def test_returns_dataframe(self):
        result = VolatilityTermStructure(_make_returns()).rolling_volatility()
        assert isinstance(result, pd.DataFrame)

    def test_correct_columns(self):
        result = VolatilityTermStructure(_make_returns()).rolling_volatility()
        assert list(result.columns) == ["SPY", "TLT"]


class TestTermStructure:
    def test_returns_all_tickers(self):
        result = VolatilityTermStructure(_make_returns()).term_structure()
        assert "SPY" in result
        assert "TLT" in result

    def test_has_horizon_keys(self):
        result = VolatilityTermStructure(_make_returns()).term_structure(windows=[21, 63])
        assert "21d" in result["SPY"]
        assert "63d" in result["SPY"]

    def test_vols_are_positive(self):
        result = VolatilityTermStructure(_make_returns()).term_structure()
        for ticker_vols in result.values():
            for v in ticker_vols.values():
                assert v > 0


class TestVolatilityCone:
    def test_returns_all_tickers(self):
        cone = VolatilityTermStructure(_make_returns()).volatility_cone()
        assert "SPY" in cone

    def test_has_percentiles(self):
        cone = VolatilityTermStructure(_make_returns()).volatility_cone(windows=[21])
        bands = cone["SPY"]["21d"]
        assert "p10" in bands
        assert "p50" in bands
        assert "p90" in bands
        assert "current" in bands

    def test_percentiles_ordered(self):
        cone = VolatilityTermStructure(_make_returns()).volatility_cone(windows=[21])
        bands = cone["SPY"]["21d"]
        assert bands["p10"] <= bands["p50"] <= bands["p90"]


class TestIsElevated:
    def test_returns_bools(self):
        result = VolatilityTermStructure(_make_returns()).is_elevated()
        for v in result.values():
            assert isinstance(v, bool)
