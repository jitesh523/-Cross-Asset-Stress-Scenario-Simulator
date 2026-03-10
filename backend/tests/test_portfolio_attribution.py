"""Tests for portfolio attribution analyzer."""

from backend.simulation.portfolio_attribution import PortfolioAttribution


def _make_attribution():
    pw = {"SPY": 0.50, "TLT": 0.30, "GLD": 0.20}
    bw = {"SPY": 0.40, "TLT": 0.40, "GLD": 0.20}
    pr = {"SPY": 0.12, "TLT": 0.04, "GLD": 0.08}
    br = {"SPY": 0.10, "TLT": 0.05, "GLD": 0.07}
    return PortfolioAttribution(pw, bw, pr, br)


class TestTotalReturns:
    def test_portfolio_return(self):
        pa = _make_attribution()
        ret = pa.total_portfolio_return()
        # 0.5*0.12 + 0.3*0.04 + 0.2*0.08 = 0.06 + 0.012 + 0.016 = 0.088
        assert abs(ret - 0.088) < 1e-6

    def test_benchmark_return(self):
        pa = _make_attribution()
        ret = pa.total_benchmark_return()
        # 0.4*0.10 + 0.4*0.05 + 0.2*0.07 = 0.04 + 0.02 + 0.014 = 0.074
        assert abs(ret - 0.074) < 1e-6


class TestEffects:
    def test_allocation_returns_all(self):
        result = _make_attribution().allocation_effect()
        assert set(result.keys()) == {"SPY", "TLT", "GLD"}

    def test_selection_returns_all(self):
        result = _make_attribution().selection_effect()
        assert set(result.keys()) == {"SPY", "TLT", "GLD"}

    def test_interaction_returns_all(self):
        result = _make_attribution().interaction_effect()
        assert set(result.keys()) == {"SPY", "TLT", "GLD"}


class TestFullAttribution:
    def test_has_required_keys(self):
        result = _make_attribution().attribute()
        required = {"portfolio_return", "benchmark_return", "excess_return", "assets"}
        assert required.issubset(set(result.keys()))

    def test_excess_return_correct(self):
        result = _make_attribution().attribute()
        assert abs(result["excess_return"] - (result["portfolio_return"] - result["benchmark_return"])) < 1e-6

    def test_effects_sum_to_excess(self):
        result = _make_attribution().attribute()
        effects_sum = result["total_allocation"] + result["total_selection"] + result["total_interaction"]
        assert abs(effects_sum - result["excess_return"]) < 1e-5

    def test_asset_details(self):
        result = _make_attribution().attribute()
        asset = result["assets"][0]
        required = {"asset", "portfolio_weight", "benchmark_weight", "allocation", "selection", "total_effect"}
        assert required.issubset(set(asset.keys()))

    def test_sorted_by_total_effect(self):
        result = _make_attribution().attribute()
        effects = [abs(a["total_effect"]) for a in result["assets"]]
        assert effects == sorted(effects, reverse=True)
