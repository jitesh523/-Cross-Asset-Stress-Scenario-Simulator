import pytest
import numpy as np
from backend.simulation.optimizer import PortfolioOptimizer

@pytest.fixture
def mock_portfolio_data():
    """Create basic data for testing optimization."""
    expected_returns = {
        "SPY": 0.10,  # 10%
        "TLT": 0.04,  # 4%
        "GLD": 0.02   # 2%
    }
    
    # 3x3 correlation matrix (identity = no correlation)
    correlation_matrix = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ])
    
    volatilities = {
        "SPY": 0.20,  # 20%
        "TLT": 0.10,  # 10%
        "GLD": 0.15   # 15%
    }
    
    return expected_returns, correlation_matrix, volatilities

def test_optimizer_init(mock_portfolio_data):
    """Test initialization and covariance calculation."""
    expected_returns, correlation_matrix, volatilities = mock_portfolio_data
    optimizer = PortfolioOptimizer(expected_returns, correlation_matrix, volatilities)
    
    assert optimizer.num_assets == 3
    assert optimizer.tickers == ["SPY", "TLT", "GLD"]
    
    # Covariance for SPY should be 0.2 * 0.2 = 0.04
    assert pytest.approx(optimizer.covariance[0, 0]) == 0.04
    # Covariance for TLT should be 0.1 * 0.1 = 0.01
    assert pytest.approx(optimizer.covariance[1, 1]) == 0.01
    # Off-diagonals should be 0
    assert optimizer.covariance[0, 1] == 0

def test_max_sharpe(mock_portfolio_data):
    """Test Maximum Sharpe Ratio optimization."""
    expected_returns, correlation_matrix, volatilities = mock_portfolio_data
    optimizer = PortfolioOptimizer(expected_returns, correlation_matrix, volatilities)
    
    result = optimizer.optimize_maximum_sharpe()
    
    assert result["success"] is True
    assert "weights" in result
    assert pytest.approx(sum(result["weights"].values())) == 1.0
    
    # With these returns/vols, SPY has highest Sharpe (0.1/0.2=0.5), 
    # then TLT (0.04/0.1=0.4), then GLD (0.02/0.15=0.13)
    # Since they are uncorrelated, most weight should be in SPY or TLT.
    assert result["weights"]["SPY"] > 0
    assert result["expected_return"] > 0.04

def test_min_vol(mock_portfolio_data):
    """Test Minimum Volatility optimization."""
    expected_returns, correlation_matrix, volatilities = mock_portfolio_data
    optimizer = PortfolioOptimizer(expected_returns, correlation_matrix, volatilities)
    
    result = optimizer.optimize_minimum_volatility()
    
    assert result["success"] is True
    assert pytest.approx(sum(result["weights"].values())) == 1.0
    
    # TLT has the lowest volatility (10%), so it should have the highest weight
    assert result["weights"]["TLT"] > result["weights"]["SPY"]
    assert result["weights"]["TLT"] > result["weights"]["GLD"]
    assert result["volatility"] <= 0.10

def test_portfolio_performance(mock_portfolio_data):
    """Test performance calculation for specific weights."""
    expected_returns, correlation_matrix, volatilities = mock_portfolio_data
    optimizer = PortfolioOptimizer(expected_returns, correlation_matrix, volatilities)
    
    # Equal weights
    weights = np.array([1/3, 1/3, 1/3])
    ret, vol, sharpe, es = optimizer.portfolio_performance(weights)
    
    expected_ret = (0.10 + 0.04 + 0.02) / 3
    assert pytest.approx(ret) == expected_ret
    assert vol > 0
    assert pytest.approx(sharpe) == ret / vol
    assert es < ret  # ES should be worse than mean return
