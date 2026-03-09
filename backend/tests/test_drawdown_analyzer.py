"""Tests for drawdown recovery analyzer."""

import numpy as np
import pandas as pd

from backend.simulation.drawdown_analyzer import DrawdownAnalyzer


def _make_prices_with_drawdown():
    """Create a price series with a clear drawdown and recovery."""
    # Starts at 100, rises to 120, crashes to 90, recovers to 125
    prices = np.array([100, 105, 110, 115, 120, 110, 100, 90, 95, 100, 105, 110, 115, 120, 125])
    dates = pd.date_range("2023-01-01", periods=len(prices), freq="B")
    return pd.Series(prices, index=dates, dtype=float)


def _make_monotonic_prices():
    """Prices that only go up — no drawdowns."""
    prices = np.linspace(100, 200, 20)
    dates = pd.date_range("2023-01-01", periods=len(prices), freq="B")
    return pd.Series(prices, index=dates, dtype=float)


class TestUnderwaterCurve:
    def test_no_drawdown(self):
        analyzer = DrawdownAnalyzer(_make_monotonic_prices())
        curve = analyzer.underwater_curve()
        assert (curve == 0).all()

    def test_negative_during_decline(self):
        analyzer = DrawdownAnalyzer(_make_prices_with_drawdown())
        curve = analyzer.underwater_curve()
        assert curve.min() < 0


class TestFindEvents:
    def test_finds_drawdown(self):
        analyzer = DrawdownAnalyzer(_make_prices_with_drawdown(), threshold=0.05)
        events = analyzer.find_events()
        assert len(events) >= 1

    def test_no_events_monotonic(self):
        analyzer = DrawdownAnalyzer(_make_monotonic_prices())
        events = analyzer.find_events()
        assert len(events) == 0

    def test_event_has_required_fields(self):
        analyzer = DrawdownAnalyzer(_make_prices_with_drawdown(), threshold=0.05)
        events = analyzer.find_events()
        event = events[0]
        assert "peak_date" in event
        assert "trough_date" in event
        assert "depth" in event
        assert "recovered" in event

    def test_depth_is_negative(self):
        analyzer = DrawdownAnalyzer(_make_prices_with_drawdown(), threshold=0.05)
        events = analyzer.find_events()
        assert events[0]["depth"] < 0


class TestSummary:
    def test_summary_structure(self):
        analyzer = DrawdownAnalyzer(_make_prices_with_drawdown(), threshold=0.05)
        summary = analyzer.summary()
        assert "num_events" in summary
        assert "max_drawdown" in summary
        assert "avg_drawdown" in summary
        assert "events" in summary

    def test_empty_summary(self):
        analyzer = DrawdownAnalyzer(_make_monotonic_prices())
        summary = analyzer.summary()
        assert summary["num_events"] == 0
        assert summary["max_drawdown"] == 0.0
