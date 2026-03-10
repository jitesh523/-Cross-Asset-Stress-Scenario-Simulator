"""Tests for scenario builder."""

import numpy as np

from backend.simulation.scenario_builder import ScenarioBuilder, build_crisis_scenario


class TestFluentAPI:
    def test_chaining(self):
        scenario = (
            ScenarioBuilder("Test")
            .set_description("A test")
            .add_shock("SPY", -0.20)
            .set_vol_multiplier(1.5)
            .set_duration(126)
            .build()
        )
        assert scenario["name"] == "Test"
        assert scenario["description"] == "A test"
        assert scenario["volatility_multiplier"] == 1.5
        assert scenario["duration_days"] == 126

    def test_add_shock(self):
        scenario = ScenarioBuilder("Test").add_shock("SPY", -0.20, 0.5).build()
        assert "SPY" in scenario["shocks"]
        assert scenario["shocks"]["SPY"]["return_shock"] == -0.20
        assert scenario["shocks"]["SPY"]["vol_shock"] == 0.5

    def test_multiple_shocks(self):
        scenario = ScenarioBuilder("Test").add_shock("SPY", -0.20).add_shock("TLT", 0.05).build()
        assert scenario["num_shocks"] == 2

    def test_correlation_override(self):
        scenario = ScenarioBuilder("Test").set_correlation_stress(0.8).build()
        assert scenario["correlation_override"] == 0.8


class TestValidation:
    def test_no_warnings_for_valid(self):
        warnings = ScenarioBuilder("Test").add_shock("SPY", -0.20).validate()
        assert len(warnings) == 0

    def test_warns_no_shocks(self):
        warnings = ScenarioBuilder("Test").validate()
        assert any("No asset shocks" in w for w in warnings)

    def test_warns_extreme_return(self):
        warnings = ScenarioBuilder("Test").add_shock("SPY", -1.5).validate()
        assert any("below -100%" in w for w in warnings)

    def test_warns_bad_correlation(self):
        warnings = ScenarioBuilder("Test").add_shock("SPY", -0.1).set_correlation_stress(2.0).validate()
        assert any("out of" in w for w in warnings)

    def test_warns_negative_vol(self):
        warnings = ScenarioBuilder("Test").set_vol_multiplier(-1).validate()
        assert any("positive" in w for w in warnings)


class TestBuildCrisis:
    def test_returns_scenario(self):
        np.random.seed(42)
        result = build_crisis_scenario(["SPY", "TLT", "GLD"], severity=0.5)
        assert result["name"].startswith("Crisis")
        assert len(result["shocks"]) == 3

    def test_severity_affects_vol(self):
        np.random.seed(42)
        mild = build_crisis_scenario(["SPY"], severity=0.2)
        np.random.seed(42)
        extreme = build_crisis_scenario(["SPY"], severity=0.9)
        assert extreme["volatility_multiplier"] > mild["volatility_multiplier"]

    def test_has_correlation_stress(self):
        np.random.seed(42)
        result = build_crisis_scenario(["SPY", "TLT"], severity=0.8)
        assert result["correlation_override"] is not None
        assert result["correlation_override"] > 0.5
