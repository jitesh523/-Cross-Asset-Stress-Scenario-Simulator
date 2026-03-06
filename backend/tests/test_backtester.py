"""Tests for backtesting engine."""

from backend.simulation.backtester import Backtester


def _make_backtester():
    """Create a standard backtester for testing."""
    predicted = {"SPY": -0.20, "TLT": 0.05, "GLD": 0.10, "QQQ": -0.15}
    actual = {"SPY": -0.18, "TLT": 0.03, "GLD": 0.12, "QQQ": -0.10}
    return Backtester(predicted, actual)


class TestErrorMetrics:
    """Tests for RMSE and MAE."""

    def test_rmse_positive(self):
        bt = _make_backtester()
        assert bt.rmse() > 0

    def test_mae_positive(self):
        bt = _make_backtester()
        assert bt.mae() > 0

    def test_perfect_prediction(self):
        """Zero error for perfect predictions."""
        predicted = {"SPY": -0.10, "TLT": 0.05}
        bt = Backtester(predicted, predicted)
        assert bt.rmse() == 0.0
        assert bt.mae() == 0.0

    def test_mae_leq_rmse(self):
        """MAE should always be <= RMSE."""
        bt = _make_backtester()
        assert bt.mae() <= bt.rmse()


class TestDirectionAccuracy:
    """Tests for direction accuracy."""

    def test_all_correct_directions(self):
        """Our mock data has all directions correct."""
        bt = _make_backtester()
        assert bt.direction_accuracy() == 1.0

    def test_wrong_directions(self):
        """Opposite predictions should give 0% accuracy."""
        predicted = {"SPY": 0.10, "TLT": -0.05}
        actual = {"SPY": -0.10, "TLT": 0.05}
        bt = Backtester(predicted, actual)
        assert bt.direction_accuracy() == 0.0

    def test_partial_accuracy(self):
        """One right, one wrong = 50%."""
        predicted = {"SPY": -0.10, "TLT": -0.05}
        actual = {"SPY": -0.08, "TLT": 0.03}
        bt = Backtester(predicted, actual)
        assert bt.direction_accuracy() == 0.5


class TestSeverityAccuracy:
    """Tests for severity accuracy."""

    def test_between_zero_and_one(self):
        bt = _make_backtester()
        assert 0.0 <= bt.severity_accuracy() <= 1.0

    def test_perfect_is_one(self):
        predicted = {"SPY": -0.10, "TLT": 0.05}
        bt = Backtester(predicted, predicted)
        assert bt.severity_accuracy() == 1.0


class TestPerAssetComparison:
    """Tests for per-asset breakdown."""

    def test_correct_count(self):
        bt = _make_backtester()
        result = bt.per_asset_comparison()
        assert len(result) == 4

    def test_sorted_by_abs_error(self):
        """Should be sorted by largest error first."""
        bt = _make_backtester()
        result = bt.per_asset_comparison()
        errors = [a["abs_error"] for a in result]
        assert errors == sorted(errors, reverse=True)

    def test_has_required_fields(self):
        bt = _make_backtester()
        asset = bt.per_asset_comparison()[0]
        required = {
            "ticker",
            "predicted_return",
            "actual_return",
            "error",
            "direction_correct",
        }
        assert required.issubset(set(asset.keys()))


class TestBacktest:
    """Tests for full backtest method."""

    def test_has_all_keys(self):
        result = _make_backtester().backtest()
        required = {
            "num_assets",
            "rmse",
            "mae",
            "direction_accuracy",
            "severity_accuracy",
            "overall_grade",
            "per_asset",
        }
        assert required.issubset(set(result.keys()))

    def test_grade_is_valid(self):
        result = _make_backtester().backtest()
        assert result["overall_grade"] in {"A", "B", "C", "D", "F"}

    def test_good_predictions_get_good_grade(self):
        """Our mock has close predictions — should get A or B."""
        result = _make_backtester().backtest()
        assert result["overall_grade"] in {"A", "B"}

    def test_mismatched_tickers(self):
        """Only common tickers should be used."""
        predicted = {"SPY": -0.10, "XYZ": 0.05}
        actual = {"SPY": -0.08, "ABC": 0.03}
        bt = Backtester(predicted, actual)
        assert bt.backtest()["num_assets"] == 1
