"""Main data ingestion service."""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Optional
import logging

from backend.data_ingestion.connectors.yfinance_connector import (
    YFinanceConnector,
    EQUITY_TICKERS,
    BOND_TICKERS,
    COMMODITY_TICKERS,
    CURRENCY_TICKERS,
)
from backend.data_ingestion.connectors.fred_connector import (
    FREDConnector,
    INDICATOR_IDS,
)
from backend.data_ingestion.validators import DataValidator
from backend.data_ingestion.transformers import DataTransformer
from backend.database import AssetPrice, EconomicIndicator, AssetMetadata
from backend.config import settings

logger = logging.getLogger(__name__)


class IngestionService:
    """Main service for data ingestion pipeline."""

    def __init__(self):
        """Initialize ingestion service."""
        self.yf_connector = YFinanceConnector()
        self.fred_connector = FREDConnector()
        self.validator = DataValidator()
        self.transformer = DataTransformer()

    def ingest_asset_prices(
        self,
        db: Session,
        tickers: List[str],
        asset_class: str,
        start_date: datetime,
        end_date: datetime,
        validate: bool = True
    ) -> int:
        """Ingest asset price data into database.
        
        Args:
            db: Database session
            tickers: List of ticker symbols
            asset_class: Asset class (equity, bond, commodity, currency)
            start_date: Start date for data
            end_date: End date for data
            validate: Whether to validate data
            
        Returns:
            Number of records inserted
        """
        logger.info(f"Ingesting {len(tickers)} {asset_class} tickers from {start_date} to {end_date}")
        
        # Fetch data
        df = self.yf_connector.fetch_multiple_tickers(tickers, start_date, end_date)
        
        if df.empty:
            logger.warning("No data fetched")
            return 0
        
        # Validate data
        if validate:
            is_valid, errors = self.validator.validate_price_data(df)
            if not is_valid:
                logger.warning(f"Data validation issues: {errors}")
        
        # Add asset class
        df['asset_class'] = asset_class
        
        # Insert into database
        records_inserted = 0
        for _, row in df.iterrows():
            asset_price = AssetPrice(
                ticker=row['ticker'],
                asset_class=row['asset_class'],
                date=row['date'],
                open=row.get('open'),
                high=row.get('high'),
                low=row.get('low'),
                close=row['close'],
                volume=row.get('volume'),
                adjusted_close=row.get('adjusted_close')
            )
            db.add(asset_price)
            records_inserted += 1
        
        db.commit()
        logger.info(f"Inserted {records_inserted} asset price records")
        return records_inserted

    def ingest_economic_indicators(
        self,
        db: Session,
        indicator_ids: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """Ingest economic indicator data into database.
        
        Args:
            db: Database session
            indicator_ids: List of FRED series IDs
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            Number of records inserted
        """
        logger.info(f"Ingesting {len(indicator_ids)} economic indicators from {start_date} to {end_date}")
        
        # Fetch data
        df = self.fred_connector.fetch_multiple_series(indicator_ids, start_date, end_date)
        
        if df.empty:
            logger.warning("No economic data fetched")
            return 0
        
        # Insert into database
        records_inserted = 0
        for _, row in df.iterrows():
            indicator = EconomicIndicator(
                indicator_code=row['indicator_code'],
                indicator_name=row['indicator_name'],
                date=row['date'],
                value=row['value'],
                frequency=row.get('frequency')
            )
            db.add(indicator)
            records_inserted += 1
        
        db.commit()
        logger.info(f"Inserted {records_inserted} economic indicator records")
        return records_inserted

    def ingest_asset_metadata(
        self,
        db: Session,
        tickers: List[str],
        asset_class: str
    ) -> int:
        """Ingest asset metadata into database.
        
        Args:
            db: Database session
            tickers: List of ticker symbols
            asset_class: Asset class
            
        Returns:
            Number of records inserted
        """
        logger.info(f"Ingesting metadata for {len(tickers)} {asset_class} tickers")
        
        # Fetch metadata
        metadata_list = self.yf_connector.get_multiple_ticker_info(tickers)
        
        if not metadata_list:
            logger.warning("No metadata fetched")
            return 0
        
        # Insert into database
        records_inserted = 0
        for metadata in metadata_list:
            asset_meta = AssetMetadata(
                ticker=metadata['ticker'],
                name=metadata['name'],
                asset_class=asset_class,
                sector=metadata.get('sector'),
                currency=metadata.get('currency'),
                description=metadata.get('description')
            )
            db.merge(asset_meta)  # Use merge to handle duplicates
            records_inserted += 1
        
        db.commit()
        logger.info(f"Inserted {records_inserted} asset metadata records")
        return records_inserted

    def run_full_ingestion(self, db: Session) -> Dict[str, int]:
        """Run full data ingestion pipeline.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with counts of records inserted
        """
        logger.info("Starting full data ingestion pipeline")
        
        start_date = settings.start_date
        end_date = settings.end_date
        
        results = {}
        
        # Ingest equities
        results['equities'] = self.ingest_asset_prices(
            db, EQUITY_TICKERS, 'equity', start_date, end_date
        )
        results['equity_metadata'] = self.ingest_asset_metadata(
            db, EQUITY_TICKERS, 'equity'
        )
        
        # Ingest bonds
        results['bonds'] = self.ingest_asset_prices(
            db, BOND_TICKERS, 'bond', start_date, end_date
        )
        results['bond_metadata'] = self.ingest_asset_metadata(
            db, BOND_TICKERS, 'bond'
        )
        
        # Ingest commodities
        results['commodities'] = self.ingest_asset_prices(
            db, COMMODITY_TICKERS, 'commodity', start_date, end_date
        )
        results['commodity_metadata'] = self.ingest_asset_metadata(
            db, COMMODITY_TICKERS, 'commodity'
        )
        
        # Ingest currencies
        results['currencies'] = self.ingest_asset_prices(
            db, CURRENCY_TICKERS, 'currency', start_date, end_date
        )
        results['currency_metadata'] = self.ingest_asset_metadata(
            db, CURRENCY_TICKERS, 'currency'
        )
        
        # Ingest economic indicators (only if API key is available)
        if settings.fred_api_key:
            results['economic_indicators'] = self.ingest_economic_indicators(
                db, INDICATOR_IDS, start_date, end_date
            )
        else:
            logger.warning("FRED API key not found, skipping economic indicators")
            results['economic_indicators'] = 0
        
        logger.info(f"Full ingestion completed: {results}")
        return results
