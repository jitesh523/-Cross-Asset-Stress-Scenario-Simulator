"""Tests for stress test grid."""

import numpy as np

from backend.simulation.stress_grid import StressGrid


def _make_grid():
    tickers = ["SPY", "TLT", "GLD"]
    returns = {"SPY": 0.10, "TLT": 0.03, "GLD": 0.05}
    vols = {"SPY": 0.20, "TLT": 0.10, "GLD": 0.15}
    return StressGrid(tickers, returns, vols, base_correlation=0.3)


class TestGridRun:
    def test_returns_matrix(self):
        result = _make_grid().run()
        assert "var_matrix" in result
        assert len(result["var_matrix"]) == 6  # default vol_multipliers
        assert len(result["var_matrix"][0]) == 6  # default corr_levels

    def test_custom_axes(self):
        result = _make_grid().run(vol_multipliers=[1.0, 2.0], correlation_levels=[0.0, 0.5])
        assert len(result["var_matrix"]) == 2
        assert len(result["var_matrix"][0]) == 2
        assert result["grid_size"] == 4

    def test_has_worst_and_best(self):
        result = _make_grid().run()
        assert "worst_case" in result
        assert "best_case" in result
        assert result["worst_case"]["var"] < result["best_case"]["var"]

    def test_worst_case_is_highest_stress(self):
        """Worst VaR should come from high vol + high correlation."""
        result = _make_grid().run()
        worst = result["worst_case"]
        assert worst["vol_multiplier"] >= 2.0
        assert worst["correlation"] >= 0.6

    def test_var_decreases_with_stress(self):
        """Higher vol multiplier should give worse (more negative) VaR."""
        result = _make_grid().run(vol_multipliers=[1.0, 3.0], correlation_levels=[0.5])
        assert result["var_matrix"][0][0] > result["var_matrix"][1][0]

    def test_custom_weights(self):
        weights = np.array([0.6, 0.2, 0.2])
        result = _make_grid().run(weights=weights)
        assert "var_matrix" in result


class TestBreakingPoint:
    def test_finds_break(self):
        result = _make_grid().find_breaking_point(var_threshold=-0.10)
        assert result["exceeded"] is True
        assert "breaking_vol_multiplier" in result

    def test_survives_easy_threshold(self):
        result = _make_grid().find_breaking_point(var_threshold=-5.0)
        assert result["exceeded"] is False

    def test_break_at_reasonable_params(self):
        result = _make_grid().find_breaking_point(var_threshold=-0.20)
        if result["exceeded"]:
            assert result["breaking_vol_multiplier"] >= 1.0
