"""Tests for stress test report generator."""

from backend.simulation.report_generator import StressTestReport


def _make_stats():
    """Create mock simulation statistics."""
    return [
        {
            "ticker": "SPY",
            "initial_price": 450.0,
            "mean_final_price": 420.0,
            "std_final_price": 30.0,
            "min_final_price": 350.0,
            "max_final_price": 500.0,
        },
        {
            "ticker": "TLT",
            "initial_price": 100.0,
            "mean_final_price": 105.0,
            "std_final_price": 8.0,
            "min_final_price": 85.0,
            "max_final_price": 120.0,
        },
        {
            "ticker": "GLD",
            "initial_price": 180.0,
            "mean_final_price": 195.0,
            "std_final_price": 12.0,
            "min_final_price": 165.0,
            "max_final_price": 220.0,
        },
    ]


def _make_var():
    """Create mock VaR metrics."""
    return {
        "var": -0.12,
        "cvar": -0.18,
        "var_dollar": -120000,
        "probability_loss": 0.62,
    }


class TestRiskRating:
    """Tests for risk rating classification."""

    def test_minimal_rating(self):
        report = StressTestReport([], {})
        assert report._risk_rating(0.02) == "MINIMAL"

    def test_low_rating(self):
        report = StressTestReport([], {})
        assert report._risk_rating(0.07) == "LOW"

    def test_medium_rating(self):
        report = StressTestReport([], {})
        assert report._risk_rating(0.15) == "MEDIUM"

    def test_high_rating(self):
        report = StressTestReport([], {})
        assert report._risk_rating(0.25) == "HIGH"

    def test_critical_rating(self):
        report = StressTestReport([], {})
        assert report._risk_rating(0.40) == "CRITICAL"


class TestReportGeneration:
    """Tests for full report generation."""

    def test_report_structure(self):
        """Report should contain all required sections."""
        report = StressTestReport(_make_stats(), _make_var()).generate()

        assert "scenario" in report
        assert "executive_summary" in report
        assert "asset_breakdown" in report
        assert "recommended_actions" in report

    def test_executive_summary_fields(self):
        """Executive summary should have all key metrics."""
        summary = StressTestReport(_make_stats(), _make_var()).generate()["executive_summary"]

        assert "portfolio_var_95" in summary
        assert "portfolio_cvar_95" in summary
        assert "most_affected_asset" in summary
        assert "overall_risk_rating" in summary
        assert "num_assets_analysed" in summary

    def test_most_affected_asset(self):
        """SPY has the worst return (-6.67%), it should be flagged."""
        report = StressTestReport(_make_stats(), _make_var()).generate()
        assert report["executive_summary"]["most_affected_asset"] == "SPY"

    def test_asset_breakdown_length(self):
        """Breakdown should have one entry per asset."""
        report = StressTestReport(_make_stats(), _make_var()).generate()
        assert len(report["asset_breakdown"]) == 3

    def test_recommended_actions_non_empty(self):
        """There should always be at least one recommended action."""
        report = StressTestReport(_make_stats(), _make_var()).generate()
        assert len(report["recommended_actions"]) > 0

    def test_custom_scenario_name(self):
        """Custom scenario name should appear in report."""
        report = StressTestReport(_make_stats(), _make_var(), scenario_name="2008 Crisis").generate()
        assert report["scenario"] == "2008 Crisis"
