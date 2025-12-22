"""Application configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from datetime import datetime


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/cross_asset_simulator"
    db_echo: bool = False

    # API Keys
    fred_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None

    # Data Ingestion
    data_start_date: str = "2019-01-01"
    data_end_date: str = "2024-12-31"
    data_interval: str = "1d"

    # Application
    app_name: str = "Cross-Asset Stress Scenario Simulator"
    debug: bool = False
    log_level: str = "INFO"

    @property
    def start_date(self) -> datetime:
        """Parse start date string to datetime."""
        return datetime.strptime(self.data_start_date, "%Y-%m-%d")

    @property
    def end_date(self) -> datetime:
        """Parse end date string to datetime."""
        return datetime.strptime(self.data_end_date, "%Y-%m-%d")


# Global settings instance
settings = Settings()
