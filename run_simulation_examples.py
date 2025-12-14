"""Example script demonstrating simulation engine usage."""

import sys
from pathlib import Path
import logging

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.simulation.monte_carlo import MonteCarloSimulation
from backend.simulation.historical_simulation import HistoricalSimulation
from backend.simulation.correlation_matrix import CorrelationMatrix
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_monte_carlo():
    """Example: Monte Carlo simulation."""
    logger.info("=" * 60)
    logger.info("Example 1: Monte Carlo Simulation")
    logger.info("=" * 60)
    
    # Define parameters
    initial_prices = {
        'SPY': 450.0,
        'TLT': 95.0,
        'GLD': 180.0
    }
    
    expected_returns = {
        'SPY': 0.10,   # 10% annual return
        'TLT': 0.03,   # 3% annual return
        'GLD': 0.05    # 5% annual return
    }
    
    volatilities = {
        'SPY': 0.20,   # 20% annual volatility
        'TLT': 0.10,   # 10% annual volatility
        'GLD': 0.15    # 15% annual volatility
    }
    
    # Correlation matrix
    correlation_matrix = np.array([
        [1.0,  -0.3,  0.1],   # SPY correlations
        [-0.3,  1.0, -0.1],   # TLT correlations
        [0.1,  -0.1,  1.0]    # GLD correlations
    ])
    
    # Create simulation
    mc_sim = MonteCarloSimulation(
        initial_prices=initial_prices,
        expected_returns=expected_returns,
        volatilities=volatilities,
        correlation_matrix=correlation_matrix
    )
    
    # Run simulation
    results = mc_sim.simulate(
        num_simulations=10000,
        num_days=252,  # 1 year
        random_seed=42
    )
    
    # Calculate statistics
    stats = mc_sim.calculate_statistics(results)
    print("\nSimulation Statistics:")
    print(stats.to_string(index=False))
    
    # Calculate VaR
    var_metrics = mc_sim.calculate_var(results, confidence_level=0.95)
    print("\nValue at Risk (95% confidence):")
    for key, value in var_metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")


def example_historical_simulation():
    """Example: Historical simulation."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 2: Historical Simulation")
    logger.info("=" * 60)
    
    # Generate synthetic historical returns
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=500, freq='D')
    
    historical_returns = pd.DataFrame({
        'SPY': np.random.normal(0.0004, 0.012, 500),  # Daily returns
        'TLT': np.random.normal(0.0001, 0.006, 500),
        'GLD': np.random.normal(0.0002, 0.009, 500)
    }, index=dates)
    
    initial_prices = {
        'SPY': 450.0,
        'TLT': 95.0,
        'GLD': 180.0
    }
    
    # Create simulation
    hist_sim = HistoricalSimulation(
        historical_returns=historical_returns,
        initial_prices=initial_prices
    )
    
    # Run simulation
    results = hist_sim.simulate(
        num_simulations=10000,
        num_days=252,
        block_size=5,  # 5-day blocks
        random_seed=42
    )
    
    # Calculate statistics
    stats = hist_sim.calculate_statistics(results)
    print("\nSimulation Statistics:")
    print(stats.to_string(index=False))
    
    # Calculate VaR
    var_metrics = hist_sim.calculate_var(results, confidence_level=0.95)
    print("\nValue at Risk (95% confidence):")
    for key, value in var_metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")


def example_correlation_analysis():
    """Example: Correlation matrix analysis."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 3: Correlation Analysis")
    logger.info("=" * 60)
    
    # Generate synthetic returns
    np.random.seed(42)
    returns_df = pd.DataFrame({
        'SPY': np.random.normal(0.0004, 0.012, 500),
        'TLT': np.random.normal(0.0001, 0.006, 500),
        'GLD': np.random.normal(0.0002, 0.009, 500),
        'USO': np.random.normal(0.0003, 0.020, 500)
    })
    
    # Add some correlation
    returns_df['TLT'] = -0.3 * returns_df['SPY'] + 0.7 * returns_df['TLT']
    returns_df['GLD'] = 0.2 * returns_df['SPY'] + 0.8 * returns_df['GLD']
    
    # Calculate correlation
    corr_calc = CorrelationMatrix()
    corr_matrix = corr_calc.calculate_from_returns(returns_df)
    
    print("\nCorrelation Matrix:")
    print(corr_matrix.round(3))
    
    # Get summary
    summary = corr_calc.get_correlation_summary()
    print("\nCorrelation Summary:")
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    # Get Cholesky decomposition
    cholesky = corr_calc.get_cholesky_decomposition()
    print("\nCholesky Decomposition:")
    print(cholesky.round(3))


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Cross-Asset Stress Scenario Simulator")
    print("Phase 2: Simulation Engine Examples")
    print("=" * 60)
    
    # Run examples
    example_monte_carlo()
    example_historical_simulation()
    example_correlation_analysis()
    
    print("\n" + "=" * 60)
    print("Examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
