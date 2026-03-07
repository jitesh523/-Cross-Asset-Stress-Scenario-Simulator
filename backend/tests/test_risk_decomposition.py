"""Tests for risk contribution decomposition."""

import numpy as np

from backend.simulation.risk_decomposition import RiskDecomposition


def _make_decomp():
    """Create a standard 3-asset decomposition for testing."""
    weights = np.array([0.5, 0.3, 0.2])
    # Simple covariance matrix
    cov = np.array(
        [
            [0.04, 0.006, 0.002],
            [0.006, 0.09, 0.009],
            [0.002, 0.009, 0.01],
        ]
    )
    tickers = ["SPY", "TLT", "GLD"]
    return RiskDecomposition(weights, cov, tickers)


class TestPortfolioVolatility:
    """Tests for portfolio volatility calculation."""

    def test_positive_volatility(self):
        """Portfolio vol should be positive for non-zero weights."""
        rd = _make_decomp()
        assert rd.portfolio_volatility() > 0

    def test_single_asset(self):
        """Single asset vol should equal its own std dev."""
        w = np.array([1.0])
        cov = np.array([[0.04]])
        rd = RiskDecomposition(w, cov, ["SPY"])
        assert abs(rd.portfolio_volatility() - 0.2) < 1e-10


class TestMarginalRisk:
    """Tests for marginal risk contributions."""

    def test_correct_length(self):
        """Should return one value per asset."""
        rd = _make_decomp()
        assert len(rd.marginal_risk()) == 3

    def test_all_positive(self):
        """Marginal risk should be positive for standard assets."""
        rd = _make_decomp()
        assert np.all(rd.marginal_risk() > 0)


class TestComponentRisk:
    """Tests for component risk contributions."""

    def test_sums_to_portfolio_vol(self):
        """Component risks must sum to total portfolio volatility."""
        rd = _make_decomp()
        assert abs(np.sum(rd.component_risk()) - rd.portfolio_volatility()) < 1e-10

    def test_correct_length(self):
        rd = _make_decomp()
        assert len(rd.component_risk()) == 3


class TestPercentageContribution:
    """Tests for percentage risk contribution."""

    def test_sums_to_one(self):
        """Percentage contributions must sum to 1.0."""
        rd = _make_decomp()
        assert abs(np.sum(rd.percentage_contribution()) - 1.0) < 1e-10

    def test_all_positive(self):
        rd = _make_decomp()
        assert np.all(rd.percentage_contribution() > 0)


class TestRiskParity:
    """Tests for risk parity weight solver."""

    def test_weights_sum_to_one(self):
        """Risk parity weights must sum to 1.0."""
        rd = _make_decomp()
        rp = rd.risk_parity_weights()
        assert abs(np.sum(rp) - 1.0) < 1e-6

    def test_all_positive(self):
        """Risk parity weights should all be positive."""
        rd = _make_decomp()
        rp = rd.risk_parity_weights()
        assert np.all(rp > 0)

    def test_equal_contributions(self):
        """Risk contributions should be roughly equal under risk parity."""
        rd = _make_decomp()
        rp = rd.risk_parity_weights()

        rp_decomp = RiskDecomposition(rp, rd.cov, rd.tickers)
        pct = rp_decomp.percentage_contribution()
        # Each should be ~33.3% for 3 assets
        assert np.max(pct) - np.min(pct) < 0.05


class TestDecompose:
    """Tests for the full decompose method."""

    def test_has_required_keys(self):
        result = _make_decomp().decompose()
        assert "portfolio_volatility" in result
        assert "assets" in result
        assert "concentration_ratio" in result

    def test_asset_details(self):
        result = _make_decomp().decompose()
        asset = result["assets"][0]
        required_keys = {
            "ticker",
            "weight",
            "marginal_risk",
            "component_risk",
            "pct_contribution",
            "risk_parity_weight",
        }
        assert required_keys.issubset(set(asset.keys()))

    def test_sorted_by_contribution(self):
        """Assets should be sorted highest contribution first."""
        result = _make_decomp().decompose()
        pcts = [a["pct_contribution"] for a in result["assets"]]
        assert pcts == sorted(pcts, reverse=True)
