"""Tests for data validators."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from backend.data_ingestion.validators import DataValidator


class TestDataValidator:
    """Test cases for DataValidator class."""

    def test_check_missing_values_pass(self):
        """Test missing values check with valid data."""
        df = pd.DataFrame({
            'a': [1, 2, 3, 4, 5],
            'b': [1, 2, None, 4, 5]
        })
        
        is_valid, problematic = DataValidator.check_missing_values(df, threshold=0.3)
        assert is_valid is True
        assert len(problematic) == 0

    def test_check_missing_values_fail(self):
        """Test missing values check with too many missing values."""
        df = pd.DataFrame({
            'a': [1, 2, 3, 4, 5],
            'b': [1, None, None, None, 5]
        })
        
        is_valid, problematic = DataValidator.check_missing_values(df, threshold=0.3)
        assert is_valid is False
        assert 'b' in problematic

    def test_check_duplicates_pass(self):
        """Test duplicate check with no duplicates."""
        df = pd.DataFrame({
            'ticker': ['AAPL', 'MSFT', 'GOOGL'],
            'date': ['2024-01-01', '2024-01-01', '2024-01-01'],
            'close': [150, 250, 350]
        })
        
        is_valid, count = DataValidator.check_duplicates(df, subset=['ticker', 'date'])
        assert is_valid is True
        assert count == 0

    def test_check_duplicates_fail(self):
        """Test duplicate check with duplicates."""
        df = pd.DataFrame({
            'ticker': ['AAPL', 'AAPL', 'GOOGL'],
            'date': ['2024-01-01', '2024-01-01', '2024-01-01'],
            'close': [150, 150, 350]
        })
        
        is_valid, count = DataValidator.check_duplicates(df, subset=['ticker', 'date'])
        assert is_valid is False
        assert count == 1

    def test_validate_price_data_pass(self):
        """Test price data validation with valid data."""
        df = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [99, 100, 101],
            'close': [103, 104, 105],
            'volume': [1000, 1100, 1200]
        })
        
        is_valid, errors = DataValidator.validate_price_data(df)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_price_data_fail_negative(self):
        """Test price data validation with negative prices."""
        df = pd.DataFrame({
            'open': [100, -101, 102],
            'high': [105, 106, 107],
            'low': [99, 100, 101],
            'close': [103, 104, 105]
        })
        
        is_valid, errors = DataValidator.validate_price_data(df)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_price_data_fail_ohlc(self):
        """Test price data validation with invalid OHLC relationships."""
        df = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [110, 100, 101],  # Low > High
            'close': [103, 104, 105]
        })
        
        is_valid, errors = DataValidator.validate_price_data(df)
        assert is_valid is False
        assert len(errors) > 0

    def test_check_outliers_iqr(self):
        """Test outlier detection using IQR method."""
        df = pd.DataFrame({
            'value': [1, 2, 3, 4, 5, 100]  # 100 is an outlier
        })
        
        has_no_outliers, outliers = DataValidator.check_outliers(df, 'value', method='iqr')
        assert has_no_outliers is False
        assert outliers.sum() > 0

    def test_check_outliers_zscore(self):
        """Test outlier detection using Z-score method."""
        df = pd.DataFrame({
            'value': [1, 2, 3, 4, 5, 100]  # 100 is an outlier
        })
        
        has_no_outliers, outliers = DataValidator.check_outliers(df, 'value', method='zscore', threshold=2.0)
        assert has_no_outliers is False
        assert outliers.sum() > 0
