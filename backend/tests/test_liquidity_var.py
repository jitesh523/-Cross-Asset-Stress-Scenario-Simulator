"""Tests for liquidity-adjusted VaR."""

from backend.simulation.liquidity_var import LiquidityAdjustedVaR


def _make_lvar():
    tickers = ["SPY", "TLT", "BTC"]
    values = {"SPY": 500000, "TLT": 300000, "BTC": 200000}
    volumes = {"SPY": 50000000, "TLT": 10000000, "BTC": 2000000}
    spreads = {"SPY": 0.0002, "TLT": 0.0005, "BTC": 0.003}
    vols = {"SPY": 0.012, "TLT": 0.007, "BTC": 0.04}
    return LiquidityAdjustedVaR(tickers, values, volumes, spreads, vols)


class TestSpreadCost:
    def test_positive(self):
        cost = _make_lvar().spread_cost("SPY")
        assert cost > 0

    def test_proportional_to_spread(self):
        lvar = _make_lvar()
        # BTC has wider spread than SPY, and smaller position but 15x wider spread
        btc_cost_per_dollar = lvar.spread_cost("BTC") / lvar.values["BTC"]
        spy_cost_per_dollar = lvar.spread_cost("SPY") / lvar.values["SPY"]
        assert btc_cost_per_dollar > spy_cost_per_dollar


class TestMarketImpact:
    def test_positive(self):
        impact = _make_lvar().market_impact("BTC")
        assert impact > 0

    def test_liquid_has_less_impact(self):
        lvar = _make_lvar()
        # SPY is highly liquid, BTC less so
        spy_impact = lvar.market_impact("SPY") / lvar.values["SPY"]
        btc_impact = lvar.market_impact("BTC") / lvar.values["BTC"]
        assert spy_impact < btc_impact


class TestStandardVaR:
    def test_positive(self):
        assert _make_lvar().standard_var() > 0

    def test_higher_confidence_higher_var(self):
        lvar = _make_lvar()
        assert lvar.standard_var(0.99) > lvar.standard_var(0.95)


class TestAdjustedVaR:
    def test_exceeds_standard(self):
        lvar = _make_lvar()
        assert lvar.adjusted_var() > lvar.standard_var()

    def test_difference_is_liquidity_cost(self):
        lvar = _make_lvar()
        diff = lvar.adjusted_var() - lvar.standard_var()
        total_liq = sum(lvar.liquidity_cost(t) for t in lvar.tickers)
        assert abs(diff - total_liq) < 0.01


class TestDecomposition:
    def test_has_required_keys(self):
        result = _make_lvar().decomposition()
        required = {"portfolio_value", "standard_var", "liquidity_adjusted_var", "assets", "liquidity_premium_pct"}
        assert required.issubset(set(result.keys()))

    def test_lvar_equals_components(self):
        result = _make_lvar().decomposition()
        expected = result["standard_var"] + result["spread_cost_total"] + result["impact_cost_total"]
        assert abs(result["liquidity_adjusted_var"] - expected) < 0.01

    def test_asset_details(self):
        result = _make_lvar().decomposition()
        asset = result["assets"][0]
        assert "ticker" in asset
        assert "spread_cost" in asset
        assert "market_impact" in asset
        assert "liquidity_grade" in asset

    def test_liquidity_grades_valid(self):
        result = _make_lvar().decomposition()
        valid_grades = {"EXCELLENT", "GOOD", "MODERATE", "POOR", "ILLIQUID"}
        for asset in result["assets"]:
            assert asset["liquidity_grade"] in valid_grades

    def test_sorted_by_cost(self):
        result = _make_lvar().decomposition()
        costs = [a["total_liquidity_cost"] for a in result["assets"]]
        assert costs == sorted(costs, reverse=True)
