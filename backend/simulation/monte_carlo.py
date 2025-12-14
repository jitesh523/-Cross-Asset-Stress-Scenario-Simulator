"""Monte Carlo simulation using Geometric Brownian Motion."""

import numpy as np
import pandas as pd
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MonteCarloSimulation:
    """Monte Carlo simulation for asset price paths using Geometric Brownian Motion."""

    def __init__(
        self,
        initial_prices: Dict[str, float],
        expected_returns: Dict[str, float],
        volatilities: Dict[str, float],
        correlation_matrix: Optional[np.ndarray] = None
    ):
        """Initialize Monte Carlo simulation.
        
        Args:
            initial_prices: Dictionary of ticker -> initial price
            expected_returns: Dictionary of ticker -> expected annual return (mu)
            volatilities: Dictionary of ticker -> annual volatility (sigma)
            correlation_matrix: Optional correlation matrix for correlated simulations
        """
        self.tickers = list(initial_prices.keys())
        self.initial_prices = np.array([initial_prices[t] for t in self.tickers])
        self.expected_returns = np.array([expected_returns[t] for t in self.tickers])
        self.volatilities = np.array([volatilities[t] for t in self.tickers])
        self.correlation_matrix = correlation_matrix
        
        logger.info(f"Initialized Monte Carlo simulation for {len(self.tickers)} assets")

    def simulate(
        self,
        num_simulations: int = 1000,
        num_days: int = 252,
        dt: float = 1/252,
        random_seed: Optional[int] = None
    ) -> Dict[str, np.ndarray]:
        """Run Monte Carlo simulation.
        
        Args:
            num_simulations: Number of simulation paths
            num_days: Number of time steps (trading days)
            dt: Time step size (1/252 for daily with annual parameters)
            random_seed: Random seed for reproducibility
            
        Returns:
            Dictionary with simulation results:
                - 'prices': 3D array (num_assets, num_simulations, num_days)
                - 'returns': 3D array of returns
                - 'final_prices': 2D array (num_assets, num_simulations)
        """
        if random_seed is not None:
            np.random.seed(random_seed)
        
        logger.info(f"Running {num_simulations} simulations for {num_days} days")
        
        num_assets = len(self.tickers)
        
        # Initialize price paths
        prices = np.zeros((num_assets, num_simulations, num_days + 1))
        prices[:, :, 0] = self.initial_prices[:, np.newaxis]
        
        # Generate random shocks
        if self.correlation_matrix is not None:
            # Correlated random variables using Cholesky decomposition
            cholesky = np.linalg.cholesky(self.correlation_matrix)
            random_shocks = self._generate_correlated_shocks(
                num_assets, num_simulations, num_days, cholesky
            )
        else:
            # Independent random variables
            random_shocks = np.random.normal(0, 1, (num_assets, num_simulations, num_days))
        
        # Simulate price paths using Geometric Brownian Motion
        # dS = S * (mu * dt + sigma * sqrt(dt) * dW)
        for t in range(num_days):
            drift = (self.expected_returns[:, np.newaxis] - 0.5 * self.volatilities[:, np.newaxis]**2) * dt
            diffusion = self.volatilities[:, np.newaxis] * np.sqrt(dt) * random_shocks[:, :, t]
            
            prices[:, :, t + 1] = prices[:, :, t] * np.exp(drift + diffusion)
        
        # Calculate returns
        returns = np.diff(np.log(prices), axis=2)
        
        results = {
            'prices': prices,
            'returns': returns,
            'final_prices': prices[:, :, -1],
            'tickers': self.tickers
        }
        
        logger.info("Monte Carlo simulation completed")
        return results

    def _generate_correlated_shocks(
        self,
        num_assets: int,
        num_simulations: int,
        num_days: int,
        cholesky: np.ndarray
    ) -> np.ndarray:
        """Generate correlated random shocks.
        
        Args:
            num_assets: Number of assets
            num_simulations: Number of simulation paths
            num_days: Number of time steps
            cholesky: Cholesky decomposition of correlation matrix
            
        Returns:
            Correlated random shocks
        """
        # Generate independent standard normal variables
        independent_shocks = np.random.normal(0, 1, (num_assets, num_simulations, num_days))
        
        # Apply Cholesky transformation for each time step
        correlated_shocks = np.zeros_like(independent_shocks)
        for t in range(num_days):
            for s in range(num_simulations):
                correlated_shocks[:, s, t] = cholesky @ independent_shocks[:, s, t]
        
        return correlated_shocks

    def calculate_statistics(self, results: Dict) -> pd.DataFrame:
        """Calculate summary statistics from simulation results.
        
        Args:
            results: Results dictionary from simulate()
            
        Returns:
            DataFrame with statistics for each asset
        """
        final_prices = results['final_prices']
        
        stats_list = []
        for i, ticker in enumerate(self.tickers):
            final_prices_asset = final_prices[i, :]
            
            stats = {
                'ticker': ticker,
                'initial_price': self.initial_prices[i],
                'mean_final_price': np.mean(final_prices_asset),
                'median_final_price': np.median(final_prices_asset),
                'std_final_price': np.std(final_prices_asset),
                'min_final_price': np.min(final_prices_asset),
                'max_final_price': np.max(final_prices_asset),
                'percentile_5': np.percentile(final_prices_asset, 5),
                'percentile_95': np.percentile(final_prices_asset, 95),
                'mean_return': (np.mean(final_prices_asset) - self.initial_prices[i]) / self.initial_prices[i],
                'probability_loss': np.mean(final_prices_asset < self.initial_prices[i])
            }
            stats_list.append(stats)
        
        return pd.DataFrame(stats_list)

    def get_price_paths_df(
        self,
        results: Dict,
        num_paths_to_show: int = 10
    ) -> Dict[str, pd.DataFrame]:
        """Convert simulation results to DataFrames for visualization.
        
        Args:
            results: Results dictionary from simulate()
            num_paths_to_show: Number of paths to include per asset
            
        Returns:
            Dictionary of ticker -> DataFrame with price paths
        """
        prices = results['prices']
        num_days = prices.shape[2]
        
        dfs = {}
        for i, ticker in enumerate(self.tickers):
            # Select subset of paths
            selected_paths = prices[i, :num_paths_to_show, :]
            
            # Create DataFrame
            df = pd.DataFrame(
                selected_paths.T,
                columns=[f'Path_{j+1}' for j in range(num_paths_to_show)]
            )
            df['Day'] = range(num_days)
            
            dfs[ticker] = df
        
        return dfs

    def calculate_var(
        self,
        results: Dict,
        confidence_level: float = 0.95,
        initial_portfolio_value: float = 1000000
    ) -> Dict:
        """Calculate Value at Risk (VaR) from simulation results.
        
        Args:
            results: Results dictionary from simulate()
            confidence_level: Confidence level for VaR (e.g., 0.95 for 95%)
            initial_portfolio_value: Initial portfolio value
            
        Returns:
            Dictionary with VaR metrics
        """
        final_prices = results['final_prices']
        
        # Calculate portfolio values (assuming equal weights)
        num_assets = len(self.tickers)
        weight_per_asset = initial_portfolio_value / num_assets
        
        # Portfolio value for each simulation
        portfolio_values = np.sum(
            (final_prices / self.initial_prices[:, np.newaxis]) * (weight_per_asset / num_assets),
            axis=0
        ) * num_assets
        
        # Calculate returns
        portfolio_returns = (portfolio_values - initial_portfolio_value) / initial_portfolio_value
        
        # VaR calculation
        var_percentile = (1 - confidence_level) * 100
        var = np.percentile(portfolio_returns, var_percentile)
        
        # CVaR (Conditional VaR / Expected Shortfall)
        cvar = np.mean(portfolio_returns[portfolio_returns <= var])
        
        return {
            'var': var,
            'cvar': cvar,
            'var_dollar': var * initial_portfolio_value,
            'cvar_dollar': cvar * initial_portfolio_value,
            'confidence_level': confidence_level,
            'mean_return': np.mean(portfolio_returns),
            'std_return': np.std(portfolio_returns),
            'probability_loss': np.mean(portfolio_returns < 0)
        }
