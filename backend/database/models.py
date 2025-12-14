"""Database models for the Cross-Asset Stress Scenario Simulator."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class AssetPrice(Base):
    """Historical asset price data."""

    __tablename__ = "asset_prices"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    asset_class = Column(String(50), nullable=False, index=True)  # equity, bond, commodity, currency
    date = Column(DateTime, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float, nullable=False)
    volume = Column(Float)
    adjusted_close = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_ticker_date", "ticker", "date"),
        Index("idx_asset_class_date", "asset_class", "date"),
    )

    def __repr__(self):
        return f"<AssetPrice(ticker={self.ticker}, date={self.date}, close={self.close})>"


class EconomicIndicator(Base):
    """Economic indicators data (interest rates, inflation, GDP, etc.)."""

    __tablename__ = "economic_indicators"

    id = Column(Integer, primary_key=True, index=True)
    indicator_code = Column(String(50), nullable=False, index=True)
    indicator_name = Column(String(200), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    value = Column(Float, nullable=False)
    frequency = Column(String(20))  # daily, monthly, quarterly, annual
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_indicator_date", "indicator_code", "date"),
    )

    def __repr__(self):
        return f"<EconomicIndicator(code={self.indicator_code}, date={self.date}, value={self.value})>"


class AssetMetadata(Base):
    """Metadata about assets (name, description, sector, etc.)."""

    __tablename__ = "asset_metadata"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200))
    asset_class = Column(String(50), nullable=False)
    sector = Column(String(100))
    currency = Column(String(10))
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AssetMetadata(ticker={self.ticker}, name={self.name}, class={self.asset_class})>"
