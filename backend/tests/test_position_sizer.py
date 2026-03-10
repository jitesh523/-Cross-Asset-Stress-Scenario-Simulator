"""Tests for position sizing module."""

from backend.simulation.position_sizer import PositionSizer


def _make_sizer():
    returns = {"SPY": 0.12, "TLT": 0.04, "GLD": 0.08, "BTC": 0.25}
    vols = {"SPY": 0.18, "TLT": 0.08, "GLD": 0.14, "BTC": 0.60}
    return PositionSizer(returns, vols, risk_free_rate=0.04)


class TestKellyFraction:
    def test_positive_for_excess_return(self):
        """SPY has positive excess return, should get positive Kelly."""
        k = _make_sizer().kelly_fraction("SPY")
        assert k > 0

    def test_zero_for_risk_free_return(self):
        """TLT return = risk-free, Kelly should be 0."""
        k = _make_sizer().kelly_fraction("TLT")
        assert k == 0.0

    def test_high_vol_reduces_kelly(self):
        """BTC has high vol, Kelly should be smaller despite high return."""
        sizer = _make_sizer()
        k_spy = sizer.kelly_fraction("SPY")
        k_btc = sizer.kelly_fraction("BTC")
        # SPY: (0.12-0.04)/0.18^2 = 2.47, BTC: (0.25-0.04)/0.60^2 = 0.58
        assert k_spy > k_btc


class TestFractionalKelly:
    def test_half_kelly(self):
        sizer = _make_sizer()
        full = sizer.kelly_fraction("SPY")
        half = sizer.fractional_kelly("SPY", fraction=0.5)
        assert abs(half - full * 0.5) < 1e-10

    def test_quarter_kelly(self):
        sizer = _make_sizer()
        full = sizer.kelly_fraction("SPY")
        quarter = sizer.fractional_kelly("SPY", fraction=0.25)
        assert abs(quarter - full * 0.25) < 1e-10


class TestOptimalSizes:
    def test_returns_all_assets(self):
        result = _make_sizer().optimal_sizes()
        assert len(result) == 4

    def test_capped_within_bounds(self):
        result = _make_sizer().optimal_sizes(max_position=0.30)
        for pos in result:
            assert abs(pos["capped_position"]) <= 0.30 + 1e-10

    def test_sorted_by_sharpe(self):
        result = _make_sizer().optimal_sizes()
        sharpes = [p["sharpe_ratio"] for p in result]
        assert sharpes == sorted(sharpes, reverse=True)

    def test_has_signal(self):
        result = _make_sizer().optimal_sizes()
        for pos in result:
            assert pos["signal"] in {"OVERWEIGHT", "UNDERWEIGHT", "NEUTRAL"}


class TestPortfolioSummary:
    def test_has_required_keys(self):
        result = _make_sizer().portfolio_summary()
        required = {"positions", "total_allocated", "cash_reserve", "long_exposure", "gross_exposure"}
        assert required.issubset(set(result.keys()))

    def test_cash_plus_allocated_leq_one(self):
        result = _make_sizer().portfolio_summary()
        assert result["cash_reserve"] + result["total_allocated"] >= 0.99

    def test_custom_fraction(self):
        conservative = _make_sizer().portfolio_summary(kelly_fraction=0.25)
        aggressive = _make_sizer().portfolio_summary(kelly_fraction=0.75)
        assert conservative["total_allocated"] <= aggressive["total_allocated"]
