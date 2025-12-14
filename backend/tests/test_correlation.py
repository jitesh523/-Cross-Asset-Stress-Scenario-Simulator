"""Tests for correlation matrix calculator."""

import pytest
import numpy as np
import pandas as pd

from backend.simulation.correlation_matrix import CorrelationMatrix


class TestCorrelationMatrix:
    """Test cases for correlation matrix calculator."""

    def test_calculate_from_returns(self):
        """Test correlation calculation from returns DataFrame."""
        # Create sample returns data
        np.random.seed(42)
        returns_df = pd.DataFrame({
            'AAPL': np.random.normal(0, 0.01, 100),
            'MSFT': np.random.normal(0, 0.01, 100),
            'GOOGL': np.random.normal(0, 0.01, 100)
        })
        
        corr_calc = CorrelationMatrix()
        corr_matrix = corr_calc.calculate_from_returns(returns_df)
        
        assert corr_matrix.shape == (3, 3)
        assert list(corr_matrix.columns) == ['AAPL', 'MSFT', 'GOOGL']
        # Diagonal should be 1
        assert np.allclose(np.diag(corr_matrix.values), 1.0)
        # Matrix should be symmetric
        assert np.allclose(corr_matrix.values, corr_matrix.values.T)

    def test_get_cholesky_decomposition(self):
        """Test Cholesky decomposition."""
        # Create a simple correlation matrix
        returns_df = pd.DataFrame({
            'A': [0.01, 0.02, -0.01, 0.03],
            'B': [0.02, 0.01, -0.02, 0.02]
        })
        
        corr_calc = CorrelationMatrix()
        corr_calc.calculate_from_returns(returns_df)
        cholesky = corr_calc.get_cholesky_decomposition()
        
        # Verify L @ L.T = correlation matrix
        reconstructed = cholesky @ cholesky.T
        assert np.allclose(reconstructed, corr_calc.correlation_matrix.values, atol=1e-10)

    def test_make_positive_definite(self):
        """Test making a matrix positive definite."""
        # Create a non-positive definite matrix
        matrix = np.array([
            [1.0, 0.9, 0.9],
            [0.9, 1.0, 0.9],
            [0.9, 0.9, 1.0]
        ])
        
        corr_calc = CorrelationMatrix()
        adjusted = corr_calc._make_positive_definite(matrix)
        
        # Check eigenvalues are positive
        eigenvalues = np.linalg.eigvalsh(adjusted)
        assert np.all(eigenvalues > 0)
        
        # Diagonal should still be 1
        assert np.allclose(np.diag(adjusted), 1.0)

    def test_get_correlation(self):
        """Test getting correlation between two assets."""
        returns_df = pd.DataFrame({
            'AAPL': [0.01, 0.02, -0.01],
            'MSFT': [0.02, 0.01, -0.02]
        })
        
        corr_calc = CorrelationMatrix()
        corr_calc.calculate_from_returns(returns_df)
        
        corr = corr_calc.get_correlation('AAPL', 'MSFT')
        assert isinstance(corr, (float, np.floating))
        assert -1 <= corr <= 1

    def test_get_average_correlation(self):
        """Test average correlation calculation."""
        returns_df = pd.DataFrame({
            'A': [0.01, 0.02, -0.01],
            'B': [0.02, 0.01, -0.02],
            'C': [0.01, -0.01, 0.02]
        })
        
        corr_calc = CorrelationMatrix()
        corr_calc.calculate_from_returns(returns_df)
        
        avg_corr = corr_calc.get_average_correlation()
        assert isinstance(avg_corr, (float, np.floating))
        assert -1 <= avg_corr <= 1

    def test_get_correlation_summary(self):
        """Test correlation summary statistics."""
        returns_df = pd.DataFrame({
            'A': [0.01, 0.02, -0.01],
            'B': [0.02, 0.01, -0.02],
            'C': [0.01, -0.01, 0.02]
        })
        
        corr_calc = CorrelationMatrix()
        corr_calc.calculate_from_returns(returns_df)
        
        summary = corr_calc.get_correlation_summary()
        
        assert 'mean' in summary
        assert 'median' in summary
        assert 'std' in summary
        assert 'min' in summary
        assert 'max' in summary
        assert 'num_assets' in summary
        assert summary['num_assets'] == 3
