"""Yahoo Finance data connector using yfinance library."""

import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class YFinanceConnector:
    """Connector for fetching data from Yahoo Finance."""

    def __init__(self):
        """Initialize YFinance connector."""
        self.session = None

    def fetch_historical_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """Fetch historical price data for a single ticker.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'SPY')
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval (1d, 1wk, 1mo, etc.)
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        try:
            logger.info(f"Fetching data for {ticker} from {start_date} to {end_date}")
            
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=False
            )
            
            if df.empty:
                logger.warning(f"No data found for {ticker}")
                return None
            
            # Rename columns to match our schema
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
                'Adj Close': 'adjusted_close'
            })
            
            # Add ticker column
            df['ticker'] = ticker
            df['date'] = df.index
            
            # Reset index
            df = df.reset_index(drop=True)
            
            logger.info(f"Fetched {len(df)} records for {ticker}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return None

    def fetch_multiple_tickers(
        self,
        tickers: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Fetch historical data for multiple tickers.
        
        Args:
            tickers: List of ticker symbols
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval
            
        Returns:
            Combined DataFrame with all tickers
        """
        all_data = []
        
        for ticker in tickers:
            df = self.fetch_historical_data(ticker, start_date, end_date, interval)
            if df is not None:
                all_data.append(df)
        
        if not all_data:
            logger.warning("No data fetched for any ticker")
            return pd.DataFrame()
        
        combined_df = pd.concat(all_data, ignore_index=True)
        logger.info(f"Fetched total {len(combined_df)} records for {len(all_data)} tickers")
        
        return combined_df

    def get_ticker_info(self, ticker: str) -> Optional[Dict]:
        """Get metadata information for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with ticker information or None if error
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            
            return {
                'ticker': ticker,
                'name': info.get('longName', info.get('shortName', ticker)),
                'sector': info.get('sector', 'Unknown'),
                'currency': info.get('currency', 'USD'),
                'description': info.get('longBusinessSummary', '')[:500]  # Limit to 500 chars
            }
        except Exception as e:
            logger.error(f"Error fetching info for {ticker}: {e}")
            return None

    def get_multiple_ticker_info(self, tickers: List[str]) -> List[Dict]:
        """Get metadata for multiple tickers.
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            List of dictionaries with ticker information
        """
        info_list = []
        
        for ticker in tickers:
            info = self.get_ticker_info(ticker)
            if info:
                info_list.append(info)
        
        return info_list


# Predefined asset lists
EQUITY_TICKERS = [
    'SPY',   # S&P 500 ETF
    'QQQ',   # Nasdaq 100 ETF
    'DIA',   # Dow Jones ETF
    'IWM',   # Russell 2000 ETF
    'AAPL',  # Apple
    'MSFT',  # Microsoft
    'GOOGL', # Google
    'AMZN',  # Amazon
]

BOND_TICKERS = [
    'TLT',   # 20+ Year Treasury Bond ETF
    'IEF',   # 7-10 Year Treasury Bond ETF
    'SHY',   # 1-3 Year Treasury Bond ETF
    'LQD',   # Investment Grade Corporate Bond ETF
    'HYG',   # High Yield Corporate Bond ETF
]

COMMODITY_TICKERS = [
    'GLD',   # Gold ETF
    'SLV',   # Silver ETF
    'USO',   # Oil ETF
    'DBA',   # Agriculture ETF
]

CURRENCY_TICKERS = [
    'EURUSD=X',  # Euro/USD
    'GBPUSD=X',  # British Pound/USD
    'JPYUSD=X',  # Japanese Yen/USD
    'AUDUSD=X',  # Australian Dollar/USD
]

ALL_TICKERS = EQUITY_TICKERS + BOND_TICKERS + COMMODITY_TICKERS + CURRENCY_TICKERS
