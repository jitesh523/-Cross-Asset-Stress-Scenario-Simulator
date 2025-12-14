"""Data validation utilities."""

import pandas as pd
import numpy as np
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates data quality and consistency."""

    @staticmethod
    def check_missing_values(df: pd.DataFrame, threshold: float = 0.3) -> Tuple[bool, List[str]]:
        """Check for missing values in DataFrame.
        
        Args:
            df: DataFrame to check
            threshold: Maximum allowed proportion of missing values (0-1)
            
        Returns:
            Tuple of (is_valid, list of problematic columns)
        """
        missing_ratio = df.isnull().sum() / len(df)
        problematic_cols = missing_ratio[missing_ratio > threshold].index.tolist()
        
        if problematic_cols:
            logger.warning(f"Columns with >{threshold*100}% missing values: {problematic_cols}")
            return False, problematic_cols
        
        return True, []

    @staticmethod
    def check_duplicates(df: pd.DataFrame, subset: List[str] = None) -> Tuple[bool, int]:
        """Check for duplicate rows.
        
        Args:
            df: DataFrame to check
            subset: Columns to check for duplicates
            
        Returns:
            Tuple of (has_no_duplicates, number of duplicates)
        """
        duplicates = df.duplicated(subset=subset).sum()
        
        if duplicates > 0:
            logger.warning(f"Found {duplicates} duplicate rows")
            return False, duplicates
        
        return True, 0

    @staticmethod
    def check_date_continuity(df: pd.DataFrame, date_column: str = 'date') -> Tuple[bool, List]:
        """Check for gaps in date series.
        
        Args:
            df: DataFrame with date column
            date_column: Name of the date column
            
        Returns:
            Tuple of (is_continuous, list of gaps)
        """
        if date_column not in df.columns:
            logger.error(f"Date column '{date_column}' not found")
            return False, []
        
        df_sorted = df.sort_values(date_column)
        dates = pd.to_datetime(df_sorted[date_column])
        
        # Calculate expected business days (for market data)
        date_range = pd.bdate_range(start=dates.min(), end=dates.max())
        missing_dates = date_range.difference(dates)
        
        if len(missing_dates) > 0:
            logger.info(f"Found {len(missing_dates)} missing business days")
            return False, missing_dates.tolist()
        
        return True, []

    @staticmethod
    def check_outliers(
        df: pd.DataFrame,
        column: str,
        method: str = 'iqr',
        threshold: float = 3.0
    ) -> Tuple[bool, pd.Series]:
        """Check for outliers in a column.
        
        Args:
            df: DataFrame to check
            column: Column name to check
            method: Method to use ('iqr' or 'zscore')
            threshold: Threshold for outlier detection
            
        Returns:
            Tuple of (has_no_outliers, boolean series marking outliers)
        """
        if column not in df.columns:
            logger.error(f"Column '{column}' not found")
            return True, pd.Series([False] * len(df))
        
        values = df[column].dropna()
        
        if method == 'iqr':
            Q1 = values.quantile(0.25)
            Q3 = values.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            outliers = (df[column] < lower_bound) | (df[column] > upper_bound)
        
        elif method == 'zscore':
            z_scores = np.abs((values - values.mean()) / values.std())
            outliers = z_scores > threshold
        
        else:
            logger.error(f"Unknown method: {method}")
            return True, pd.Series([False] * len(df))
        
        outlier_count = outliers.sum()
        if outlier_count > 0:
            logger.info(f"Found {outlier_count} outliers in '{column}' using {method} method")
            return False, outliers
        
        return True, outliers

    @staticmethod
    def validate_price_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate price data integrity.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Tuple of (is_valid, list of validation errors)
        """
        errors = []
        
        # Check required columns
        required_cols = ['open', 'high', 'low', 'close']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
            return False, errors
        
        # Check for negative prices
        for col in required_cols:
            if (df[col] < 0).any():
                errors.append(f"Negative values found in '{col}'")
        
        # Check OHLC relationships
        if not ((df['high'] >= df['low']).all()):
            errors.append("High price is less than low price in some rows")
        
        if not ((df['high'] >= df['open']).all() and (df['high'] >= df['close']).all()):
            errors.append("High price is less than open/close in some rows")
        
        if not ((df['low'] <= df['open']).all() and (df['low'] <= df['close']).all()):
            errors.append("Low price is greater than open/close in some rows")
        
        # Check for zero volume (if volume exists)
        if 'volume' in df.columns:
            zero_volume_count = (df['volume'] == 0).sum()
            if zero_volume_count > len(df) * 0.1:  # More than 10% zero volume
                errors.append(f"High number of zero volume days: {zero_volume_count}")
        
        if errors:
            for error in errors:
                logger.warning(f"Price data validation error: {error}")
            return False, errors
        
        return True, []
