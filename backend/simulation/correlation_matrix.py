"""Correlation matrix calculation and management."""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
import logging

from backend.database import AssetPrice

logger = logging.getLogger(__name__)


class CorrelationMatrix:
    """Calculate and manage correlation matrices for multi-asset simulation."""

    def __init__(self):
        """Initialize correlation matrix calculator."""
        self.correlation_matrix = None
        self.tickers = []

    def calculate_from_returns(
        self,
        returns_df: pd.DataFrame,
        method: str = 'pearson'
    ) -> pd.DataFrame:
        """Calculate correlation matrix from returns data.
        
        Args:
            returns_df: DataFrame with returns for multiple assets (columns = tickers)
            method: Correlation method ('pearson', 'kendall', 'spearman')
            
        Returns:
            Correlation matrix as DataFrame
        """
        logger.info(f"Calculating {method} correlation matrix for {len(returns_df.columns)} assets")
        
        # Calculate correlation
        corr_matrix = returns_df.corr(method=method)
        
        self.correlation_matrix = corr_matrix
        self.tickers = list(corr_matrix.columns)
        
        logger.info(f"Correlation matrix calculated: {corr_matrix.shape}")
        return corr_matrix

    def calculate_from_database(
        self,
        db: Session,
        tickers: List[str],
        start_date: str,
        end_date: str,
        method: str = 'pearson'
    ) -> pd.DataFrame:
        """Calculate correlation matrix from database data.
        
        Args:
            db: Database session
            tickers: List of ticker symbols
            start_date: Start date for data
            end_date: End date for data
            method: Correlation method
            
        Returns:
            Correlation matrix as DataFrame
        """
        logger.info(f"Fetching data for {len(tickers)} tickers from database")
        
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
            logger.warning("No data found in database")
            return pd.DataFrame()
        
        # Combine data
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Pivot to wide format
        price_df = combined_df.pivot(index='date', columns='ticker', values='close')
        
        # Calculate returns
        returns_df = price_df.pct_change().dropna()
        
        # Calculate correlation
        return self.calculate_from_returns(returns_df, method=method)

    def get_cholesky_decomposition(self) -> np.ndarray:
        """Get Cholesky decomposition of correlation matrix.
        
        Used for generating correlated random variables in Monte Carlo simulation.
        
        Returns:
            Lower triangular Cholesky matrix
        """
        if self.correlation_matrix is None:
            raise ValueError("Correlation matrix not calculated yet")
        
        try:
            cholesky = np.linalg.cholesky(self.correlation_matrix.values)
            logger.info("Cholesky decomposition calculated successfully")
            return cholesky
        except np.linalg.LinAlgError:
            logger.warning("Correlation matrix is not positive definite, using eigenvalue adjustment")
            # Adjust matrix to be positive definite
            adjusted_matrix = self._make_positive_definite(self.correlation_matrix.values)
            cholesky = np.linalg.cholesky(adjusted_matrix)
            return cholesky

    def _make_positive_definite(self, matrix: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
        """Make a matrix positive definite by adjusting eigenvalues.
        
        Args:
            matrix: Input correlation matrix
            epsilon: Minimum eigenvalue threshold
            
        Returns:
            Adjusted positive definite matrix
        """
        # Eigenvalue decomposition
        eigenvalues, eigenvectors = np.linalg.eigh(matrix)
        
        # Adjust negative eigenvalues
        eigenvalues[eigenvalues < epsilon] = epsilon
        
        # Reconstruct matrix
        adjusted_matrix = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
        
        # Normalize to correlation matrix (diagonal = 1)
        d = np.sqrt(np.diag(adjusted_matrix))
        adjusted_matrix = adjusted_matrix / np.outer(d, d)
        
        return adjusted_matrix

    def get_correlation(self, ticker1: str, ticker2: str) -> float:
        """Get correlation between two assets.
        
        Args:
            ticker1: First ticker symbol
            ticker2: Second ticker symbol
            
        Returns:
            Correlation coefficient
        """
        if self.correlation_matrix is None:
            raise ValueError("Correlation matrix not calculated yet")
        
        return self.correlation_matrix.loc[ticker1, ticker2]

    def get_average_correlation(self) -> float:
        """Get average correlation across all asset pairs.
        
        Returns:
            Average correlation coefficient
        """
        if self.correlation_matrix is None:
            raise ValueError("Correlation matrix not calculated yet")
        
        # Get upper triangle (excluding diagonal)
        mask = np.triu(np.ones_like(self.correlation_matrix), k=1).astype(bool)
        correlations = self.correlation_matrix.values[mask]
        
        return np.mean(correlations)

    def get_correlation_summary(self) -> Dict:
        """Get summary statistics of correlation matrix.
        
        Returns:
            Dictionary with correlation statistics
        """
        if self.correlation_matrix is None:
            raise ValueError("Correlation matrix not calculated yet")
        
        # Get upper triangle (excluding diagonal)
        mask = np.triu(np.ones_like(self.correlation_matrix), k=1).astype(bool)
        correlations = self.correlation_matrix.values[mask]
        
        return {
            'mean': np.mean(correlations),
            'median': np.median(correlations),
            'std': np.std(correlations),
            'min': np.min(correlations),
            'max': np.max(correlations),
            'num_assets': len(self.tickers)
        }

    def export_to_csv(self, filepath: str):
        """Export correlation matrix to CSV file.
        
        Args:
            filepath: Path to save CSV file
        """
        if self.correlation_matrix is None:
            raise ValueError("Correlation matrix not calculated yet")
        
        self.correlation_matrix.to_csv(filepath)
        logger.info(f"Correlation matrix exported to {filepath}")

    def load_from_csv(self, filepath: str):
        """Load correlation matrix from CSV file.
        
        Args:
            filepath: Path to CSV file
        """
        self.correlation_matrix = pd.read_csv(filepath, index_col=0)
        self.tickers = list(self.correlation_matrix.columns)
        logger.info(f"Correlation matrix loaded from {filepath}")
