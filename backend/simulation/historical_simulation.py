"""Historical simulation using bootstrap resampling."""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from backend.database import AssetPrice

logger = logging.getLogger(__name__)


class HistoricalSimulation:
    """Historical simulation using bootstrap resampling of historical returns."""

    def __init__(
        self,
        historical_returns: pd.DataFrame,
        initial_prices: Dict[str, float]
    ):
        """Initialize historical simulation.
        
        Args:
            historical_returns: DataFrame with historical returns (columns = tickers)
            initial_prices: Dictionary of ticker -> initial price
        """
        self.historical_returns = historical_returns
        self.tickers = list(historical_returns.columns)
        self.initial_prices = np.array([initial_prices[t] for t in self.tickers])
        
        logger.info(f"Initialized historical simulation with {len(historical_returns)} historical periods")

    @classmethod
    def from_database(
        cls,
        db: Session,
        tickers: List[str],
        start_date: str,
        end_date: str,
        initial_prices: Dict[str, float]
    ):
        """Create historical simulation from database data.
        
        Args:
            db: Database session
            tickers: List of ticker symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            initial_prices: Dictionary of ticker -> initial price
            
        Returns:
            HistoricalSimulation instance
        """
        logger.info(f"Loading historical data for {len(tickers)} tickers from database")
        
        # Fetch price data
        all_data = []
        for ticker in tickers:
            query = db.query(AssetPrice).filter(
                AssetPrice.ticker == ticker,
                AssetPrice.date >= start_date,
                AssetPrice.date <= end_date
            ).order_by(AssetPrice.date)
            
            data = query.all()
            if data:
                df = pd.DataFrame([{
                    'date': d.date,
                    'close': d.close,
                    'ticker': d.ticker
                } for d in data])
                all_data.append(df)
        
        if not all_data:
            raise ValueError("No historical data found in database")
        
        # Combine data
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Pivot to wide format
        price_df = combined_df.pivot(index='date', columns='ticker', values='close')
        
        # Calculate returns
        returns_df = price_df.pct_change().dropna()
        
        return cls(returns_df, initial_prices)

    def simulate(
        self,
        num_simulations: int = 1000,
        num_days: int = 252,
        block_size: int = 1,
        random_seed: Optional[int] = None
    ) -> Dict[str, np.ndarray]:
        """Run historical simulation using bootstrap resampling.
        
        Args:
            num_simulations: Number of simulation paths
            num_days: Number of time steps to simulate
            block_size: Block size for block bootstrap (1 = standard bootstrap)
            random_seed: Random seed for reproducibility
            
        Returns:
            Dictionary with simulation results:
                - 'prices': 3D array (num_assets, num_simulations, num_days)
                - 'returns': 3D array of returns
                - 'final_prices': 2D array (num_assets, num_simulations)
        """
        if random_seed is not None:
            np.random.seed(random_seed)
        
        logger.info(f"Running {num_simulations} historical simulations for {num_days} days")
        
        num_assets = len(self.tickers)
        num_historical_periods = len(self.historical_returns)
        
        # Initialize price paths
        prices = np.zeros((num_assets, num_simulations, num_days + 1))
        prices[:, :, 0] = self.initial_prices[:, np.newaxis]
        
        # Initialize returns array
        simulated_returns = np.zeros((num_assets, num_simulations, num_days))
        
        if block_size == 1:
            # Standard bootstrap: sample individual days
            for sim in range(num_simulations):
                # Randomly sample days from historical returns
                sampled_indices = np.random.randint(0, num_historical_periods, size=num_days)
                sampled_returns = self.historical_returns.iloc[sampled_indices].values.T
                simulated_returns[:, sim, :] = sampled_returns
        else:
            # Block bootstrap: sample blocks of consecutive days
            for sim in range(num_simulations):
                sampled_returns = self._block_bootstrap(num_days, block_size, num_historical_periods)
                simulated_returns[:, sim, :] = sampled_returns
        
        # Calculate price paths from returns
        for t in range(num_days):
            prices[:, :, t + 1] = prices[:, :, t] * (1 + simulated_returns[:, :, t])
        
        results = {
            'prices': prices,
            'returns': simulated_returns,
            'final_prices': prices[:, :, -1],
            'tickers': self.tickers
        }
        
        logger.info("Historical simulation completed")
        return results

    def _block_bootstrap(
        self,
        num_days: int,
        block_size: int,
        num_historical_periods: int
    ) -> np.ndarray:
        """Perform block bootstrap resampling.
        
        Args:
            num_days: Number of days to simulate
            block_size: Size of each block
            num_historical_periods: Total number of historical periods
            
        Returns:
            Sampled returns array (num_assets, num_days)
        """
        sampled_returns = []
        days_sampled = 0
        
        while days_sampled < num_days:
            # Randomly select a starting point for the block
            max_start = num_historical_periods - block_size
            if max_start <= 0:
                # If block size is larger than historical data, use standard bootstrap
                start_idx = np.random.randint(0, num_historical_periods)
                block = self.historical_returns.iloc[start_idx:start_idx+1].values.T
            else:
                start_idx = np.random.randint(0, max_start)
                block = self.historical_returns.iloc[start_idx:start_idx+block_size].values.T
            
            sampled_returns.append(block)
            days_sampled += block.shape[1]
        
        # Concatenate and trim to exact length
        all_returns = np.concatenate(sampled_returns, axis=1)[:, :num_days]
        
        return all_returns

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

    def get_empirical_distribution(self, results: Dict, ticker: str) -> Dict:
        """Get empirical distribution of final prices for a specific asset.
        
        Args:
            results: Results dictionary from simulate()
            ticker: Ticker symbol
            
        Returns:
            Dictionary with distribution information
        """
        ticker_idx = self.tickers.index(ticker)
        final_prices = results['final_prices'][ticker_idx, :]
        
        # Calculate histogram
        hist, bin_edges = np.histogram(final_prices, bins=50)
        
        return {
            'ticker': ticker,
            'histogram': hist,
            'bin_edges': bin_edges,
            'mean': np.mean(final_prices),
            'median': np.median(final_prices),
            'std': np.std(final_prices),
            'skewness': self._calculate_skewness(final_prices),
            'kurtosis': self._calculate_kurtosis(final_prices)
        }

    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate skewness of distribution."""
        mean = np.mean(data)
        std = np.std(data)
        return np.mean(((data - mean) / std) ** 3)

    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate kurtosis of distribution."""
        mean = np.mean(data)
        std = np.std(data)
        return np.mean(((data - mean) / std) ** 4) - 3  # Excess kurtosis
