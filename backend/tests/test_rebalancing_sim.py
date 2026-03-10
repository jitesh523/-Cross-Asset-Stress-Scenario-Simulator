"""Tests for multi-period rebalancing simulator."""

from backend.simulation.rebalancing_sim import RebalancingSimulator


def _make_sim():
    targets = {"SPY": 0.50, "TLT": 0.30, "GLD": 0.20}
    returns = {"SPY": 0.10, "TLT": 0.03, "GLD": 0.06}
    vols = {"SPY": 0.18, "TLT": 0.08, "GLD": 0.14}
    return RebalancingSimulator(targets, returns, vols, initial_value=1000000)


class TestSimulate:
    def test_returns_result(self):
        result = _make_sim().simulate(num_periods=6, seed=42)
        assert "final_value" in result
        assert "total_return_pct" in result
        assert "periods" in result

    def test_correct_num_periods(self):
        result = _make_sim().simulate(num_periods=6, seed=42)
        assert len(result["periods"]) == 6

    def test_period_has_required_fields(self):
        result = _make_sim().simulate(num_periods=4, seed=42)
        period = result["periods"][0]
        required = {"period", "portfolio_value", "period_return", "max_drift", "rebalanced", "weights"}
        assert required.issubset(set(period.keys()))

    def test_reproducible_with_seed(self):
        r1 = _make_sim().simulate(num_periods=6, seed=42)
        r2 = _make_sim().simulate(num_periods=6, seed=42)
        assert r1["final_value"] == r2["final_value"]

    def test_different_seeds_differ(self):
        r1 = _make_sim().simulate(num_periods=6, seed=42)
        r2 = _make_sim().simulate(num_periods=6, seed=99)
        assert r1["final_value"] != r2["final_value"]

    def test_weights_sum_to_one(self):
        result = _make_sim().simulate(num_periods=6, seed=42)
        for p in result["periods"]:
            total = sum(p["weights"].values())
            assert abs(total - 1.0) < 0.01

    def test_no_rebalance_mode(self):
        result = _make_sim().simulate(num_periods=6, rebalance=False, seed=42)
        assert result["num_rebalances"] == 0


class TestCompareStrategies:
    def test_has_both_strategies(self):
        result = _make_sim().compare_strategies(num_periods=12, seed=42)
        assert "rebalanced" in result
        assert "buy_and_hold" in result
        assert "rebalancing_benefit_pct" in result

    def test_benefit_is_difference(self):
        result = _make_sim().compare_strategies(num_periods=12, seed=42)
        expected_diff = round(result["rebalanced"]["total_return_pct"] - result["buy_and_hold"]["total_return_pct"], 2)
        assert result["rebalancing_benefit_pct"] == expected_diff
