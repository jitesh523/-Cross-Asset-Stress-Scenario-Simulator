"""Tests for market regime detector."""

import numpy as np
import pandas as pd

from backend.simulation.regime_detector import RegimeDetector


def _make_returns(n=500, seed=42):
    """Generate synthetic return data with different market phases."""
    np.random.seed(seed)

    # Bull: low vol, positive drift
    bull = np.random.normal(0.0008, 0.008, 200)
    # Crisis: very negative, high vol
    crisis = np.random.normal(-0.015, 0.035, 50)
    # Recovery: positive drift, high vol
    recovery = np.random.normal(0.003, 0.020, 100)
    # Bear: slight negative, moderate vol
    bear = np.random.normal(-0.002, 0.015, 150)

    returns = np.concatenate([bull, crisis, recovery, bear])
    dates = pd.date_range("2020-01-01", periods=len(returns), freq="B")
    return pd.DataFrame({"SPY": returns}, index=dates)


class TestRegimeDetection:
    """Tests for regime classification."""

    def test_detect_returns_dataframe(self):
        """detect() should return a DataFrame with required columns."""
        df = _make_returns()
        detector = RegimeDetector(df)
        result = detector.detect()

        assert isinstance(result, pd.DataFrame)
        assert "rolling_vol" in result.columns
        assert "rolling_return" in result.columns
        assert "regime" in result.columns

    def test_all_regimes_valid(self):
        """All regime labels should be one of the known types."""
        df = _make_returns()
        detector = RegimeDetector(df)
        result = detector.detect()

        valid = {"BULL", "BEAR", "CRISIS", "RECOVERY"}
        assert set(result["regime"].unique()).issubset(valid)

    def test_detects_multiple_regimes(self):
        """With synthetic data, multiple regimes should be detected."""
        df = _make_returns()
        detector = RegimeDetector(df)
        result = detector.detect()

        unique_regimes = result["regime"].nunique()
        assert unique_regimes >= 2

    def test_crisis_detection(self):
        """A severe crash should produce CRISIS or BEAR labels."""
        df = _make_returns()
        detector = RegimeDetector(df)
        result = detector.detect()

        # The crisis period (rows 200-250) should show up as CRISIS or BEAR
        negative_regimes = result["regime"].isin(["CRISIS", "BEAR"]).sum()
        assert negative_regimes > 0


class TestRegimeSummary:
    """Tests for regime summary statistics."""

    def test_summary_structure(self):
        """Summary should have total_periods and regimes dict."""
        df = _make_returns()
        detector = RegimeDetector(df)
        summary = detector.summary()

        assert "total_periods" in summary
        assert "regimes" in summary
        assert isinstance(summary["regimes"], dict)

    def test_summary_percentages_sum(self):
        """Regime percentages should sum to approximately 100."""
        df = _make_returns()
        detector = RegimeDetector(df)
        summary = detector.summary()

        total_pct = sum(r["percentage"] for r in summary["regimes"].values())
        assert abs(total_pct - 100.0) < 1.0

    def test_summary_has_stats(self):
        """Each regime entry should have avg_volatility and avg_return."""
        df = _make_returns()
        detector = RegimeDetector(df)
        summary = detector.summary()

        for regime_data in summary["regimes"].values():
            assert "avg_volatility" in regime_data
            assert "avg_return" in regime_data
            assert "count" in regime_data

    def test_multi_asset(self):
        """Detector should handle multi-column DataFrames."""
        np.random.seed(42)
        n = 300
        dates = pd.date_range("2020-01-01", periods=n, freq="B")
        df = pd.DataFrame(
            {
                "SPY": np.random.normal(0.0005, 0.01, n),
                "TLT": np.random.normal(0.0002, 0.005, n),
            },
            index=dates,
        )
        detector = RegimeDetector(df)
        result = detector.detect()

        assert len(result) > 0
        assert "regime" in result.columns
