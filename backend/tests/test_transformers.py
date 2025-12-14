"""Tests for data transformers."""

import pytest
import pandas as pd
import numpy as np

from backend.data_ingestion.transformers import DataTransformer


class TestDataTransformer:
    """Test cases for DataTransformer class."""

    def test_calculate_returns_log(self):
        """Test log returns calculation."""
        df = pd.DataFrame({
            'close': [100, 110, 105, 115]
        })
        
        result = DataTransformer.calculate_returns(df, method='log')
        
        assert 'returns' in result.columns
        assert pd.isna(result['returns'].iloc[0])  # First value should be NaN
        assert not pd.isna(result['returns'].iloc[1])

    def test_calculate_returns_simple(self):
        """Test simple returns calculation."""
        df = pd.DataFrame({
            'close': [100, 110, 105, 115]
        })
        
        result = DataTransformer.calculate_returns(df, method='simple')
        
        assert 'returns' in result.columns
        assert pd.isna(result['returns'].iloc[0])
        assert abs(result['returns'].iloc[1] - 0.1) < 0.001  # 10% return

    def test_handle_missing_values_ffill(self):
        """Test forward fill for missing values."""
        df = pd.DataFrame({
            'value': [1, 2, None, None, 5]
        })
        
        result = DataTransformer.handle_missing_values(df, method='ffill')
        
        assert result['value'].isna().sum() == 0
        assert result['value'].iloc[2] == 2

    def test_handle_missing_values_interpolate(self):
        """Test interpolation for missing values."""
        df = pd.DataFrame({
            'value': [1, 2, None, 4, 5]
        })
        
        result = DataTransformer.handle_missing_values(df, method='interpolate')
        
        assert result['value'].isna().sum() == 0
        assert result['value'].iloc[2] == 3

    def test_normalize_data_zscore(self):
        """Test z-score normalization."""
        df = pd.DataFrame({
            'value': [1, 2, 3, 4, 5]
        })
        
        result = DataTransformer.normalize_data(df, columns=['value'], method='zscore')
        
        assert 'value_normalized' in result.columns
        assert abs(result['value_normalized'].mean()) < 0.001  # Mean should be ~0
        assert abs(result['value_normalized'].std() - 1.0) < 0.001  # Std should be ~1

    def test_normalize_data_minmax(self):
        """Test min-max normalization."""
        df = pd.DataFrame({
            'value': [1, 2, 3, 4, 5]
        })
        
        result = DataTransformer.normalize_data(df, columns=['value'], method='minmax')
        
        assert 'value_normalized' in result.columns
        assert result['value_normalized'].min() == 0
        assert result['value_normalized'].max() == 1

    def test_calculate_volatility(self):
        """Test volatility calculation."""
        np.random.seed(42)
        returns = np.random.normal(0, 0.01, 100)
        df = pd.DataFrame({'returns': returns})
        
        result = DataTransformer.calculate_volatility(df, window=21, annualize=True)
        
        assert 'volatility' in result.columns
        assert result['volatility'].iloc[-1] > 0

    def test_resample_data(self):
        """Test data resampling."""
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'open': range(100, 110),
            'high': range(105, 115),
            'low': range(95, 105),
            'close': range(102, 112),
            'volume': [1000] * 10
        })
        
        result = DataTransformer.resample_data(df, frequency='W')
        
        assert len(result) < len(df)
        assert 'close' in result.columns

    def test_add_technical_indicators(self):
        """Test adding technical indicators."""
        df = pd.DataFrame({
            'close': [100 + i for i in range(250)]
        })
        
        result = DataTransformer.add_technical_indicators(df)
        
        assert 'sma_20' in result.columns
        assert 'sma_50' in result.columns
        assert 'ema_12' in result.columns
        assert 'macd' in result.columns
        assert 'rsi' in result.columns
