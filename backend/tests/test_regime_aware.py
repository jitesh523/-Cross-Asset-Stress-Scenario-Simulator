import pytest
import numpy as np
from backend.simulation.monte_carlo import MonteCarloSimulation

def test_regime_aware_convergence():
    initial_prices = {"A": 100, "B": 100}
    # Zero returns, high-ish volatility
    expected_returns = {"A": 0.0, "B": 0.0}
    volatilities = {"A": 0.3, "B": 0.3}
    # No initial correlation
    correlation_matrix = np.array([[1.0, 0.0], [0.0, 1.0]])
    
    mc = MonteCarloSimulation(initial_prices, expected_returns, volatilities, correlation_matrix)
    
    # Run Normal
    results_normal = mc.simulate(num_simulations=1000, num_days=20, random_seed=42, regime_aware=False)
    returns_normal = results_normal['returns']
    corr_normal = np.corrcoef(returns_normal[0].flatten(), returns_normal[1].flatten())[0, 1]
    
    # Run Regime-Aware
    results_regime = mc.simulate(num_simulations=1000, num_days=20, random_seed=42, regime_aware=True)
    returns_regime = results_regime['returns']
    corr_regime = np.corrcoef(returns_regime[0].flatten(), returns_regime[1].flatten())[0, 1]
    
    # In regime-aware, correlation should have drifted upward due to stress paths
    # Note: We use the same seed, so the shocks are the same, but the transformation changes.
    assert corr_regime > corr_normal
    print(f"Normal Corr: {corr_normal:.4f}, Regime-Aware Corr: {corr_regime:.4f}")
