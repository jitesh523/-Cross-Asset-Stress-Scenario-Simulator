"""FRED (Federal Reserve Economic Data) connector."""

from fredapi import Fred
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


class FREDConnector:
    """Connector for fetching economic data from FRED API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize FRED connector.
        
        Args:
            api_key: FRED API key. If None, uses settings.
        """
        self.api_key = api_key or settings.fred_api_key
        if not self.api_key:
            logger.warning("FRED API key not provided. Set FRED_API_KEY in .env file.")
            self.fred = None
        else:
            self.fred = Fred(api_key=self.api_key)

    def fetch_series(
        self,
        series_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Fetch a single economic indicator series.
        
        Args:
            series_id: FRED series ID (e.g., 'DFF' for Federal Funds Rate)
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            DataFrame with date and value columns or None if error
        """
        if not self.fred:
            logger.error("FRED API not initialized. Check API key.")
            return None

        try:
            logger.info(f"Fetching FRED series {series_id} from {start_date} to {end_date}")
            
            series = self.fred.get_series(
                series_id,
                observation_start=start_date,
                observation_end=end_date
            )
            
            if series.empty:
                logger.warning(f"No data found for series {series_id}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame({
                'date': series.index,
                'value': series.values,
                'indicator_code': series_id
            })
            
            # Get series info for metadata
            info = self.fred.get_series_info(series_id)
            df['indicator_name'] = info.get('title', series_id)
            df['frequency'] = info.get('frequency_short', 'Unknown')
            
            logger.info(f"Fetched {len(df)} records for {series_id}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching FRED series {series_id}: {e}")
            return None

    def fetch_multiple_series(
        self,
        series_ids: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Fetch multiple economic indicator series.
        
        Args:
            series_ids: List of FRED series IDs
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            Combined DataFrame with all series
        """
        all_data = []
        
        for series_id in series_ids:
            df = self.fetch_series(series_id, start_date, end_date)
            if df is not None:
                all_data.append(df)
        
        if not all_data:
            logger.warning("No data fetched for any series")
            return pd.DataFrame()
        
        combined_df = pd.concat(all_data, ignore_index=True)
        logger.info(f"Fetched total {len(combined_df)} records for {len(all_data)} series")
        
        return combined_df

    def search_series(self, search_text: str, limit: int = 10) -> List[Dict]:
        """Search for FRED series by keyword.
        
        Args:
            search_text: Search keyword
            limit: Maximum number of results
            
        Returns:
            List of dictionaries with series information
        """
        if not self.fred:
            logger.error("FRED API not initialized. Check API key.")
            return []

        try:
            results = self.fred.search(search_text, limit=limit)
            
            series_list = []
            for _, row in results.iterrows():
                series_list.append({
                    'id': row.get('id'),
                    'title': row.get('title'),
                    'frequency': row.get('frequency_short'),
                    'units': row.get('units_short'),
                    'popularity': row.get('popularity', 0)
                })
            
            return series_list
            
        except Exception as e:
            logger.error(f"Error searching FRED series: {e}")
            return []


# Predefined economic indicators
ECONOMIC_INDICATORS = {
    # Interest Rates
    'DFF': 'Federal Funds Effective Rate',
    'DGS10': '10-Year Treasury Constant Maturity Rate',
    'DGS2': '2-Year Treasury Constant Maturity Rate',
    'T10Y2Y': '10-Year Treasury Minus 2-Year Treasury',
    
    # Inflation
    'CPIAUCSL': 'Consumer Price Index for All Urban Consumers',
    'CPILFESL': 'Consumer Price Index Less Food and Energy',
    'PCEPI': 'Personal Consumption Expenditures Price Index',
    
    # Economic Activity
    'GDP': 'Gross Domestic Product',
    'UNRATE': 'Unemployment Rate',
    'PAYEMS': 'All Employees: Total Nonfarm',
    'INDPRO': 'Industrial Production Index',
    
    # Market Indicators
    'VIXCLS': 'CBOE Volatility Index: VIX',
    'DEXUSEU': 'U.S. / Euro Foreign Exchange Rate',
    'DCOILWTICO': 'Crude Oil Prices: West Texas Intermediate',
}

INDICATOR_IDS = list(ECONOMIC_INDICATORS.keys())
