import pytest
from backend.simulation.hedging_service import HedgingService

def test_hedging_calculation():
    tickers = ["AAPL", "GOOGL"]
    hedger = HedgingService(tickers, initial_total_value=100000.0)
    
    current_weights = {"AAPL": 0.5, "GOOGL": 0.5}
    target_weights = {"AAPL": 0.3, "GOOGL": 0.7}
    
    trades = hedger.calculate_trades(current_weights, target_weights)
    
    assert len(trades) == 2
    
    # Check SELL
    sell_trade = next(t for t in trades if t["action"] == "SELL")
    assert sell_trade["ticker"] == "AAPL"
    assert sell_trade["weight_change"] == pytest.approx(0.2)
    assert sell_trade["dollar_value"] == pytest.approx(20000.0)
    
    # Check BUY
    buy_trade = next(t for t in trades if t["action"] == "BUY")
    assert buy_trade["ticker"] == "GOOGL"
    assert buy_trade["weight_change"] == pytest.approx(0.2)
    assert buy_trade["dollar_value"] == pytest.approx(20000.0)

def test_generate_recommendations():
    tickers = ["AAPL", "GOOGL"]
    hedger = HedgingService(tickers)
    
    opt_result = {
        "success": True,
        "weights": {"AAPL": 0.6, "GOOGL": 0.4}
    }
    
    # Starting from equal weights (0.5, 0.5)
    result = hedger.generate_recommendations(opt_result)
    
    assert "trades" in result
    assert result["total_value"] == 1000000.0
    assert len(result["trades"]) == 2
    
    aapl_trade = next(t for t in result["trades"] if t["ticker"] == "AAPL")
    assert aapl_trade["action"] == "BUY"
    assert aapl_trade["target_weight"] == 0.6
