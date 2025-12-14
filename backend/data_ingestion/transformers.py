"""Data transformation utilities."""

import pandas as pd
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transforms and processes financial data."""

    @staticmethod
    def calculate_returns(
        df: pd.DataFrame,
        price_column: str = 'close',
        method: str = 'log',
        periods: int = 1
    ) -> pd.DataFrame:
        """Calculate returns from price data.
        
        Args:
            df: DataFrame with price data
            price_column: Column containing prices
            method: 'log' for log returns or 'simple' for simple returns
            periods: Number of periods for return calculation
            
        Returns:
            DataFrame with returns column added
        """
        df = df.copy()
        
        if price_column not in df.columns:
            logger.error(f"Column '{price_column}' not found")
            return df
        
        if method == 'log':
            df['returns'] = np.log(df[price_column] / df[price_column].shift(periods))
        elif method == 'simple':
            df['returns'] = df[price_column].pct_change(periods=periods)
        else:
            logger.error(f"Unknown method: {method}")
            return df
        
        logger.info(f"Calculated {method} returns with {periods} period(s)")
        return df

    @staticmethod
    def handle_missing_values(
        df: pd.DataFrame,
        method: str = 'ffill',
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Handle missing values in DataFrame.
        
        Args:
            df: DataFrame with missing values
            method: Method to use ('ffill', 'bfill', 'interpolate', 'drop')
            limit: Maximum number of consecutive NaNs to fill
            
        Returns:
            DataFrame with missing values handled
        """
        df = df.copy()
        
        if method == 'ffill':
            df = df.fillna(method='ffill', limit=limit)
        elif method == 'bfill':
            df = df.fillna(method='bfill', limit=limit)
        elif method == 'interpolate':
            df = df.interpolate(method='linear', limit=limit)
        elif method == 'drop':
            df = df.dropna()
        else:
            logger.error(f"Unknown method: {method}")
            return df
        
        logger.info(f"Handled missing values using {method} method")
        return df

    @staticmethod
    def normalize_data(
        df: pd.DataFrame,
        columns: list,
        method: str = 'zscore'
    ) -> pd.DataFrame:
        """Normalize data columns.
        
        Args:
            df: DataFrame to normalize
            columns: List of columns to normalize
            method: Normalization method ('zscore', 'minmax', 'robust')
            
        Returns:
            DataFrame with normalized columns
        """
        df = df.copy()
        
        for col in columns:
            if col not in df.columns:
                logger.warning(f"Column '{col}' not found, skipping")
                continue
            
            if method == 'zscore':
                df[f'{col}_normalized'] = (df[col] - df[col].mean()) / df[col].std()
            elif method == 'minmax':
                df[f'{col}_normalized'] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
            elif method == 'robust':
                median = df[col].median()
                q75, q25 = df[col].quantile([0.75, 0.25])
                iqr = q75 - q25
                df[f'{col}_normalized'] = (df[col] - median) / iqr
            else:
                logger.error(f"Unknown method: {method}")
                continue
        
        logger.info(f"Normalized {len(columns)} columns using {method} method")
        return df

    @staticmethod
    def calculate_volatility(
        df: pd.DataFrame,
        returns_column: str = 'returns',
        window: int = 21,
        annualize: bool = True
    ) -> pd.DataFrame:
        """Calculate rolling volatility.
        
        Args:
            df: DataFrame with returns
            returns_column: Column containing returns
            window: Rolling window size (default 21 for monthly)
            annualize: Whether to annualize volatility
            
        Returns:
            DataFrame with volatility column added
        """
        df = df.copy()
        
        if returns_column not in df.columns:
            logger.error(f"Column '{returns_column}' not found")
            return df
        
        df['volatility'] = df[returns_column].rolling(window=window).std()
        
        if annualize:
            df['volatility'] = df['volatility'] * np.sqrt(252)  # Assuming daily data
        
        logger.info(f"Calculated {window}-period rolling volatility")
        return df

    @staticmethod
    def resample_data(
        df: pd.DataFrame,
        date_column: str = 'date',
        frequency: str = 'W',
        aggregation: dict = None
    ) -> pd.DataFrame:
        """Resample time series data to different frequency.
        
        Args:
            df: DataFrame with time series data
            date_column: Column containing dates
            frequency: Target frequency ('D', 'W', 'M', 'Q', 'Y')
            aggregation: Dictionary mapping columns to aggregation functions
            
        Returns:
            Resampled DataFrame
        """
        df = df.copy()
        
        if date_column not in df.columns:
            logger.error(f"Date column '{date_column}' not found")
            return df
        
        # Set date as index
        df[date_column] = pd.to_datetime(df[date_column])
        df = df.set_index(date_column)
        
        # Default aggregation
        if aggregation is None:
            aggregation = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }
        
        # Filter aggregation to only include existing columns
        aggregation = {k: v for k, v in aggregation.items() if k in df.columns}
        
        # Resample
        df_resampled = df.resample(frequency).agg(aggregation)
        df_resampled = df_resampled.reset_index()
        
        logger.info(f"Resampled data to {frequency} frequency")
        return df_resampled

    @staticmethod
    def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add common technical indicators.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with technical indicators added
        """
        df = df.copy()
        
        # Simple Moving Averages
        if 'close' in df.columns:
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # Exponential Moving Average
        if 'close' in df.columns:
            df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        if 'ema_12' in df.columns and 'ema_26' in df.columns:
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        # RSI (Relative Strength Index)
        if 'close' in df.columns:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
        
        logger.info("Added technical indicators")
        return df
