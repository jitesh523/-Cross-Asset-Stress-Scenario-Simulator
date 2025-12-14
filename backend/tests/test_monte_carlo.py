"""Tests for Monte Carlo simulation."""

import pytest
import numpy as np
import pandas as pd

from backend.simulation.monte_carlo import MonteCarloSimulation


class TestMonteCarloSimulation:
    """Test cases for Monte Carlo simulation."""

    def test_initialization(self):
        """Test Monte Carlo simulation initialization."""
        initial_prices = {'AAPL': 150.0, 'MSFT': 250.0}
        expected_returns = {'AAPL': 0.10, 'MSFT': 0.12}
        volatilities = {'AAPL': 0.25, 'MSFT': 0.30}
        
        mc_sim = MonteCarloSimulation(
            initial_prices=initial_prices,
            expected_returns=expected_returns,
            volatilities=volatilities
        )
        
        assert len(mc_sim.tickers) == 2
        assert mc_sim.tickers == ['AAPL', 'MSFT']
        assert np.allclose(mc_sim.initial_prices, [150.0, 250.0])

    def test_simulate_basic(self):
        """Test basic simulation without correlation."""
        initial_prices = {'AAPL': 150.0}
        expected_returns = {'AAPL': 0.10}
        volatilities = {'AAPL': 0.25}
        
        mc_sim = MonteCarloSimulation(
            initial_prices=initial_prices,
            expected_returns=expected_returns,
            volatilities=volatilities
        )
        
        results = mc_sim.simulate(
            num_simulations=100,
            num_days=10,
            random_seed=42
        )
        
        assert 'prices' in results
        assert 'returns' in results
        assert 'final_prices' in results
        assert results['prices'].shape == (1, 100, 11)  # 1 asset, 100 sims, 11 days (including initial)
        assert results['returns'].shape == (1, 100, 10)

    def test_simulate_with_correlation(self):
        """Test simulation with correlation matrix."""
        initial_prices = {'AAPL': 150.0, 'MSFT': 250.0}
        expected_returns = {'AAPL': 0.10, 'MSFT': 0.12}
        volatilities = {'AAPL': 0.25, 'MSFT': 0.30}
        correlation_matrix = np.array([[1.0, 0.7], [0.7, 1.0]])
        
        mc_sim = MonteCarloSimulation(
            initial_prices=initial_prices,
            expected_returns=expected_returns,
            volatilities=volatilities,
            correlation_matrix=correlation_matrix
        )
        
        results = mc_sim.simulate(
            num_simulations=100,
            num_days=10,
            random_seed=42
        )
        
        assert results['prices'].shape == (2, 100, 11)

    def test_calculate_statistics(self):
        """Test statistics calculation."""
        initial_prices = {'AAPL': 150.0}
        expected_returns = {'AAPL': 0.10}
        volatilities = {'AAPL': 0.25}
        
        mc_sim = MonteCarloSimulation(
            initial_prices=initial_prices,
            expected_returns=expected_returns,
            volatilities=volatilities
        )
        
        results = mc_sim.simulate(num_simulations=100, num_days=10, random_seed=42)
        stats = mc_sim.calculate_statistics(results)
        
        assert len(stats) == 1
        assert 'ticker' in stats.columns
        assert 'mean_final_price' in stats.columns
        assert 'std_final_price' in stats.columns

    def test_calculate_var(self):
        """Test VaR calculation."""
        initial_prices = {'AAPL': 150.0, 'MSFT': 250.0}
        expected_returns = {'AAPL': 0.10, 'MSFT': 0.12}
        volatilities = {'AAPL': 0.25, 'MSFT': 0.30}
        
        mc_sim = MonteCarloSimulation(
            initial_prices=initial_prices,
            expected_returns=expected_returns,
            volatilities=volatilities
        )
        
        results = mc_sim.simulate(num_simulations=1000, num_days=252, random_seed=42)
        var_metrics = mc_sim.calculate_var(results, confidence_level=0.95)
        
        assert 'var' in var_metrics
        assert 'cvar' in var_metrics
        assert 'var_dollar' in var_metrics
        assert 'probability_loss' in var_metrics
        assert var_metrics['var'] < 0  # VaR should be negative (loss)

    def test_reproducibility(self):
        """Test that results are reproducible with same seed."""
        initial_prices = {'AAPL': 150.0}
        expected_returns = {'AAPL': 0.10}
        volatilities = {'AAPL': 0.25}
        
        mc_sim1 = MonteCarloSimulation(
            initial_prices=initial_prices,
            expected_returns=expected_returns,
            volatilities=volatilities
        )
        
        mc_sim2 = MonteCarloSimulation(
            initial_prices=initial_prices,
            expected_returns=expected_returns,
            volatilities=volatilities
        )
        
        results1 = mc_sim1.simulate(num_simulations=10, num_days=5, random_seed=42)
        results2 = mc_sim2.simulate(num_simulations=10, num_days=5, random_seed=42)
        
        assert np.allclose(results1['prices'], results2['prices'])
