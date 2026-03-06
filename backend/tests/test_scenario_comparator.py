"""Tests for scenario comparator."""

from backend.simulation.scenario_comparator import ScenarioComparator


def _make_scenarios():
    """Create mock scenario results for testing."""
    return [
        {
            "name": "2008 Crisis",
            "var_metrics": {"var": -0.25, "cvar": -0.35, "probability_loss": 0.80},
            "statistics": [
                {"ticker": "SPY", "initial_price": 150, "mean_final_price": 105},
                {"ticker": "TLT", "initial_price": 90, "mean_final_price": 100},
                {"ticker": "GLD", "initial_price": 100, "mean_final_price": 115},
            ],
        },
        {
            "name": "Mild Correction",
            "var_metrics": {"var": -0.05, "cvar": -0.08, "probability_loss": 0.55},
            "statistics": [
                {"ticker": "SPY", "initial_price": 450, "mean_final_price": 430},
                {"ticker": "TLT", "initial_price": 100, "mean_final_price": 102},
                {"ticker": "GLD", "initial_price": 180, "mean_final_price": 185},
            ],
        },
        {
            "name": "Rate Shock",
            "var_metrics": {"var": -0.12, "cvar": -0.18, "probability_loss": 0.65},
            "statistics": [
                {"ticker": "SPY", "initial_price": 450, "mean_final_price": 415},
                {"ticker": "TLT", "initial_price": 100, "mean_final_price": 85},
                {"ticker": "GLD", "initial_price": 180, "mean_final_price": 190},
            ],
        },
    ]


class TestCompare:
    """Tests for scenario comparison and ranking."""

    def test_returns_all_scenarios(self):
        result = ScenarioComparator(_make_scenarios()).compare()
        assert len(result) == 3

    def test_sorted_by_severity(self):
        """Scenarios should be sorted from worst to mildest."""
        result = ScenarioComparator(_make_scenarios()).compare()
        scores = [s["severity_score"] for s in result]
        assert scores == sorted(scores, reverse=True)

    def test_2008_is_worst(self):
        """2008 Crisis should rank #1 (most severe)."""
        result = ScenarioComparator(_make_scenarios()).compare()
        assert result[0]["scenario"] == "2008 Crisis"
        assert result[0]["rank"] == 1

    def test_has_required_fields(self):
        result = ScenarioComparator(_make_scenarios()).compare()
        entry = result[0]
        required = {
            "scenario",
            "severity_score",
            "portfolio_var",
            "portfolio_cvar",
            "assets_at_risk",
            "worst_asset",
            "rank",
        }
        assert required.issubset(set(entry.keys()))

    def test_assets_at_risk_count(self):
        """2008 Crisis has 1 asset losing value (SPY drops 30%)."""
        result = ScenarioComparator(_make_scenarios()).compare()
        crisis = next(s for s in result if s["scenario"] == "2008 Crisis")
        assert crisis["assets_at_risk"] == 1


class TestWorstCase:
    """Tests for worst case identification."""

    def test_returns_single_scenario(self):
        result = ScenarioComparator(_make_scenarios()).worst_case()
        assert "scenario" in result
        assert result["scenario"] == "2008 Crisis"

    def test_empty_scenarios(self):
        result = ScenarioComparator([]).worst_case()
        assert result == {}


class TestHeatmap:
    """Tests for heatmap data generation."""

    def test_correct_dimensions(self):
        hm = ScenarioComparator(_make_scenarios()).heatmap_data()
        assert len(hm["scenarios"]) == 3
        assert len(hm["assets"]) == 3  # SPY, TLT, GLD
        assert len(hm["matrix"]) == 3
        assert len(hm["matrix"][0]) == 3

    def test_assets_sorted(self):
        hm = ScenarioComparator(_make_scenarios()).heatmap_data()
        assert hm["assets"] == sorted(hm["assets"])

    def test_returns_are_floats(self):
        hm = ScenarioComparator(_make_scenarios()).heatmap_data()
        for row in hm["matrix"]:
            for val in row:
                assert isinstance(val, float)
