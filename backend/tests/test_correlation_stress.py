"""Tests for correlation stress testing utility."""

import numpy as np

from backend.simulation.correlation_stress import CorrelationStressTester


def _make_tester():
    """Create a standard 3-asset correlation stress tester."""
    corr = np.array(
        [
            [1.00, 0.30, 0.10],
            [0.30, 1.00, 0.15],
            [0.10, 0.15, 1.00],
        ]
    )
    vols = np.array([0.20, 0.15, 0.10])
    weights = np.array([0.5, 0.3, 0.2])
    tickers = ["SPY", "TLT", "GLD"]
    return CorrelationStressTester(corr, vols, weights, tickers)


class TestUniformStress:
    """Tests for uniform correlation shift."""

    def test_returns_results(self):
        results = _make_tester().stress_uniform()
        assert len(results) == 4  # default shifts

    def test_vol_increases_with_correlation(self):
        """Higher correlations should increase portfolio volatility."""
        results = _make_tester().stress_uniform()
        vols = [r["stressed_vol"] for r in results]
        assert vols == sorted(vols)

    def test_custom_shifts(self):
        results = _make_tester().stress_uniform(shifts=[0.05, 0.1])
        assert len(results) == 2

    def test_has_required_fields(self):
        result = _make_tester().stress_uniform()[0]
        assert "correlation_shift" in result
        assert "baseline_vol" in result
        assert "stressed_vol" in result
        assert "vol_change_pct" in result


class TestStressToOne:
    """Tests for perfect correlation scenario."""

    def test_returns_result(self):
        result = _make_tester().stress_to_one()
        assert "worst_case_vol" in result

    def test_worst_case_higher(self):
        """Perfect correlation should give higher vol."""
        result = _make_tester().stress_to_one()
        assert result["worst_case_vol"] >= result["baseline_vol"]

    def test_vol_increase_positive(self):
        result = _make_tester().stress_to_one()
        assert result["vol_increase_pct"] >= 0


class TestSensitivityMatrix:
    """Tests for pair sensitivity analysis."""

    def test_correct_pair_count(self):
        """3 assets should give 3 pairs."""
        result = _make_tester().sensitivity_matrix()
        assert len(result["pair_sensitivities"]) == 3

    def test_sorted_by_impact(self):
        result = _make_tester().sensitivity_matrix()
        impacts = [abs(p["vol_impact_pct"]) for p in result["pair_sensitivities"]]
        assert impacts == sorted(impacts, reverse=True)

    def test_has_pair_labels(self):
        result = _make_tester().sensitivity_matrix()
        pair = result["pair_sensitivities"][0]
        assert "/" in pair["pair"]
