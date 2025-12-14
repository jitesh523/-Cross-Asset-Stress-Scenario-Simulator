"""Script to initialize database and run data ingestion."""

import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database import db_manager
from backend.data_ingestion.ingestion_service import IngestionService
from backend.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main function to initialize database and ingest data."""
    logger.info("=" * 60)
    logger.info("Cross-Asset Stress Scenario Simulator - Data Ingestion")
    logger.info("=" * 60)
    
    # Create database tables
    logger.info("\n[1/2] Creating database tables...")
    try:
        db_manager.create_tables()
        logger.info("✓ Database tables created successfully")
    except Exception as e:
        logger.error(f"✗ Failed to create database tables: {e}")
        return
    
    # Run data ingestion
    logger.info("\n[2/2] Running data ingestion...")
    try:
        ingestion_service = IngestionService()
        
        with db_manager.get_session() as db:
            results = ingestion_service.run_full_ingestion(db)
        
        logger.info("\n" + "=" * 60)
        logger.info("Data Ingestion Results:")
        logger.info("=" * 60)
        for key, value in results.items():
            logger.info(f"  {key:.<40} {value:>6} records")
        logger.info("=" * 60)
        
        total_records = sum(results.values())
        logger.info(f"\n✓ Total records inserted: {total_records}")
        
    except Exception as e:
        logger.error(f"\n✗ Data ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    logger.info("\n✓ Data ingestion completed successfully!")
    logger.info("\nNext steps:")
    logger.info("  1. Verify data in database")
    logger.info("  2. Run tests: pytest backend/tests/")
    logger.info("  3. Proceed to Phase 2: Core Simulation Engine")


if __name__ == "__main__":
    main()
