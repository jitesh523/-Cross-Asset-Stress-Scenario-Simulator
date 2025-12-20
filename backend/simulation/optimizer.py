"""Portfolio optimization module using Mean-Variance Optimization."""

import numpy as np
import pandas as pd
import scipy.optimize as sco
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class PortfolioOptimizer:
    """Class for optimizing portfolio asset weights."""

    def __init__(self, expected_returns: Dict[str, float], correlation_matrix: np.ndarray, volatilities: Dict[str, float]):
        """Initialize optimizer with asset statistics.
        
        Args:
            expected_returns: Annualized expected returns for each asset
            correlation_matrix: Asset correlation matrix
            volatilities: Annualized volatilities for each asset
        """
        self.tickers = list(expected_returns.keys())
        self.returns = np.array([expected_returns[t] for t in self.tickers])
        self.vols = np.array([volatilities[t] for t in self.tickers])
        
        # Calculate covariance matrix
        # Cov = Diag(vols) * Corr * Diag(vols)
        diag_vols = np.diag(self.vols)
        self.covariance = diag_vols @ correlation_matrix @ diag_vols
        
        self.num_assets = len(self.tickers)

    def portfolio_performance(self, weights: np.ndarray) -> Tuple[float, float, float]:
        """Calculate portfolio annual return, volatility and Sharpe ratio.
        
        Args:
            weights: Asset weights
            
        Returns:
            Tuple of (return, volatility, Sharpe ratio)
        """
        port_return = np.sum(self.returns * weights)
        port_vol = np.sqrt(weights.T @ self.covariance @ weights)
        sharpe = port_return / port_vol if port_vol > 0 else 0
        return port_return, port_vol, sharpe

    def _neg_sharpe(self, weights: np.ndarray) -> float:
        """Negative Sharpe ratio to maximize it using minimize()."""
        return -self.portfolio_performance(weights)[2]

    def _port_vol(self, weights: np.ndarray) -> float:
        """Portfolio volatility to minimize it."""
        return self.portfolio_performance(weights)[1]

    def optimize_maximum_sharpe(self) -> Dict:
        """Find weights that maximize the Sharpe ratio.
        
        Returns:
            Optimization results
        """
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(self.num_assets))
        initial_guess = np.array(self.num_assets * [1. / self.num_assets])
        
        opts = sco.minimize(self._neg_sharpe, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        
        if not opts.success:
            logger.error(f"Optimization failed: {opts.message}")
            return {'success': False, 'message': opts.message}
            
        weights = opts.x
        ret, vol, sharpe = self.portfolio_performance(weights)
        
        return {
            'success': True,
            'weights': dict(zip(self.tickers, weights.tolist())),
            'expected_return': ret,
            'volatility': vol,
            'sharpe_ratio': sharpe
        }

    def optimize_minimum_volatility(self) -> Dict:
        """Find weights that minimize portfolio volatility.
        
        Returns:
            Optimization results
        """
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(self.num_assets))
        initial_guess = np.array(self.num_assets * [1. / self.num_assets])
        
        opts = sco.minimize(self._port_vol, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        
        if not opts.success:
            logger.error(f"Optimization failed: {opts.message}")
            return {'success': False, 'message': opts.message}
            
        weights = opts.x
        ret, vol, sharpe = self.portfolio_performance(weights)
        
        return {
            'success': True,
            'weights': dict(zip(self.tickers, weights.tolist())),
            'expected_return': ret,
            'volatility': vol,
            'sharpe_ratio': sharpe
        }
