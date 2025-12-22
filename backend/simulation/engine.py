"""Main simulation engine orchestrator."""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Literal
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from backend.simulation.monte_carlo import MonteCarloSimulation
from backend.simulation.historical_simulation import HistoricalSimulation
from backend.simulation.correlation_matrix import CorrelationMatrix
from backend.database import AssetPrice

logger = logging.getLogger(__name__)


class SimulationEngine:
    """Main simulation engine for running stress scenarios."""

    def __init__(self, db: Session):
        """Initialize simulation engine.
        
        Args:
            db: Database session
        """
        self.db = db
        self.correlation_calculator = CorrelationMatrix()

    def prepare_simulation_data(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str
    ) -> Dict:
        """Prepare data for simulation from database.
        
        Args:
            tickers: List of ticker symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            Dictionary with prepared data
        """
        logger.info(f"Preparing simulation data for {len(tickers)} tickers")
        
        # Fetch price data
        all_data = []
        for ticker in tickers:
            query = self.db.query(AssetPrice).filter(
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
            raise ValueError("No data found in database")
        
        # Combine data
        combined_df = pd.concat(all_data, ignore_index=True)
        price_df = combined_df.pivot(index='date', columns='ticker', values='close')
        
        # Calculate returns
        returns_df = price_df.pct_change().dropna()
        
        # Calculate statistics
        initial_prices = {ticker: price_df[ticker].iloc[-1] for ticker in tickers}
        expected_returns = {ticker: returns_df[ticker].mean() * 252 for ticker in tickers}  # Annualized
        volatilities = {ticker: returns_df[ticker].std() * np.sqrt(252) for ticker in tickers}  # Annualized
        
        # Calculate correlation matrix
        correlation_matrix = self.correlation_calculator.calculate_from_returns(returns_df)
        
        return {
            'price_df': price_df,
            'returns_df': returns_df,
            'initial_prices': initial_prices,
            'expected_returns': expected_returns,
            'volatilities': volatilities,
            'correlation_matrix': correlation_matrix.values,
            'tickers': tickers
        }

    def run_monte_carlo(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        num_simulations: int = 1000,
        num_days: int = 252,
        use_correlation: bool = True,
        random_seed: Optional[int] = None,
        regime_aware: bool = False,
        scenario_adjustments: Optional[Dict] = None
    ) -> Dict:
        """Run Monte Carlo simulation.
        
        Args:
            tickers: List of ticker symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            num_simulations: Number of simulation paths
            num_days: Number of days to simulate
            use_correlation: Whether to use correlation matrix
            random_seed: Random seed for reproducibility
            scenario_adjustments: Optional scenario adjustments (shocks)
            
        Returns:
            Dictionary with simulation results and statistics
        """
        logger.info(f"Running Monte Carlo simulation for {len(tickers)} assets")
        
        # Prepare data
        data = self.prepare_simulation_data(tickers, start_date, end_date)
        
        # Apply scenario adjustments if provided
        if scenario_adjustments:
            data = self._apply_scenario_adjustments(data, scenario_adjustments)
        
        # Create Monte Carlo simulation
        correlation_matrix = data['correlation_matrix'] if use_correlation else None
        
        mc_sim = MonteCarloSimulation(
            initial_prices=data['initial_prices'],
            expected_returns=data['expected_returns'],
            volatilities=data['volatilities'],
            correlation_matrix=correlation_matrix
        )
        
        # Run simulation
        results = mc_sim.simulate(
            num_simulations=num_simulations,
            num_days=num_days,
            random_seed=random_seed,
            regime_aware=regime_aware
        )
        
        # Calculate statistics
        stats = mc_sim.calculate_statistics(results)
        var_metrics = mc_sim.calculate_var(results)
        
        return {
            'method': 'monte_carlo',
            'results': results,
            'statistics': stats,
            'var_metrics': var_metrics,
            'parameters': {
                'num_simulations': num_simulations,
                'num_days': num_days,
                'use_correlation': use_correlation,
                'tickers': tickers
            }
        }

    def run_historical(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        num_simulations: int = 1000,
        num_days: int = 252,
        block_size: int = 1,
        random_seed: Optional[int] = None
    ) -> Dict:
        """Run historical simulation.
        
        Args:
            tickers: List of ticker symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            num_simulations: Number of simulation paths
            num_days: Number of days to simulate
            block_size: Block size for block bootstrap
            random_seed: Random seed for reproducibility
            
        Returns:
            Dictionary with simulation results and statistics
        """
        logger.info(f"Running historical simulation for {len(tickers)} assets")
        
        # Prepare data
        data = self.prepare_simulation_data(tickers, start_date, end_date)
        
        # Create historical simulation
        hist_sim = HistoricalSimulation(
            historical_returns=data['returns_df'],
            initial_prices=data['initial_prices']
        )
        
        # Run simulation
        results = hist_sim.simulate(
            num_simulations=num_simulations,
            num_days=num_days,
            block_size=block_size,
            random_seed=random_seed
        )
        
        # Calculate statistics
        stats = hist_sim.calculate_statistics(results)
        var_metrics = hist_sim.calculate_var(results)
        
        return {
            'method': 'historical',
            'results': results,
            'statistics': stats,
            'var_metrics': var_metrics,
            'parameters': {
                'num_simulations': num_simulations,
                'num_days': num_days,
                'block_size': block_size,
                'tickers': tickers
            }
        }

    def run_simulation(
        self,
        method: Literal['monte_carlo', 'historical'],
        tickers: List[str],
        start_date: str,
        end_date: str,
        num_simulations: int = 1000,
        num_days: int = 252,
        **kwargs
    ) -> Dict:
        """Run simulation using specified method.
        
        Args:
            method: Simulation method ('monte_carlo' or 'historical')
            tickers: List of ticker symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            num_simulations: Number of simulation paths
            num_days: Number of days to simulate
            **kwargs: Additional method-specific parameters
            
        Returns:
            Dictionary with simulation results
        """
        if method == 'monte_carlo':
            return self.run_monte_carlo(
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                num_simulations=num_simulations,
                num_days=num_days,
                **kwargs
            )
        elif method == 'historical':
            return self.run_historical(
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                num_simulations=num_simulations,
                num_days=num_days,
                **kwargs
            )
        else:
            raise ValueError(f"Unknown simulation method: {method}")

    def _apply_scenario_adjustments(self, data: Dict, adjustments: Dict) -> Dict:
        """Apply scenario adjustments (shocks) to simulation parameters.
        
        Args:
            data: Prepared simulation data
            adjustments: Dictionary with adjustments:
                - 'return_shock': Dict[ticker, shock_value] (e.g., -0.1 for -10%)
                - 'volatility_multiplier': Dict[ticker, multiplier] (e.g., 1.5 for 50% increase)
                - 'correlation_multiplier': float (e.g., 1.2 for 20% increase in correlations)
            
        Returns:
            Adjusted data dictionary
        """
        logger.info("Applying scenario adjustments")
        
        # Apply return shocks
        if 'return_shock' in adjustments:
            for ticker, shock in adjustments['return_shock'].items():
                if ticker in data['expected_returns']:
                    data['expected_returns'][ticker] += shock
                    logger.info(f"Applied return shock of {shock:.2%} to {ticker}")
        
        # Apply volatility multipliers
        if 'volatility_multiplier' in adjustments:
            for ticker, multiplier in adjustments['volatility_multiplier'].items():
                if ticker in data['volatilities']:
                    data['volatilities'][ticker] *= multiplier
                    logger.info(f"Applied volatility multiplier of {multiplier:.2f} to {ticker}")
        
        # Apply correlation multiplier
        if 'correlation_multiplier' in adjustments:
            multiplier = adjustments['correlation_multiplier']
            corr_matrix = data['correlation_matrix']
            
            # Adjust off-diagonal elements
            n = corr_matrix.shape[0]
            for i in range(n):
                for j in range(n):
                    if i != j:
                        corr_matrix[i, j] *= multiplier
                        # Ensure correlations stay within [-1, 1]
                        corr_matrix[i, j] = np.clip(corr_matrix[i, j], -0.99, 0.99)
            
            # Make matrix positive definite if needed
            data['correlation_matrix'] = self.correlation_calculator._make_positive_definite(corr_matrix)
            logger.info(f"Applied correlation multiplier of {multiplier:.2f}")
        
        return data

    def compare_methods(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        num_simulations: int = 1000,
        num_days: int = 252
    ) -> Dict:
        """Compare Monte Carlo and Historical simulation methods.
        
        Args:
            tickers: List of ticker symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            num_simulations: Number of simulation paths
            num_days: Number of days to simulate
            
        Returns:
            Dictionary with comparison results
        """
        logger.info("Comparing Monte Carlo and Historical simulation methods")
        
        # Run both methods
        mc_results = self.run_monte_carlo(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            num_simulations=num_simulations,
            num_days=num_days,
            random_seed=42
        )
        
        hist_results = self.run_historical(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            num_simulations=num_simulations,
            num_days=num_days,
            random_seed=42
        )
        
        # Compare statistics
        comparison = {
            'monte_carlo': {
                'statistics': mc_results['statistics'],
                'var_metrics': mc_results['var_metrics']
            },
            'historical': {
                'statistics': hist_results['statistics'],
                'var_metrics': hist_results['var_metrics']
            }
        }
        
        return comparison
