# Cross-Asset Stress Scenario Simulator

A comprehensive tool for simulating stress scenarios across multiple asset classes (equities, bonds, commodities, currencies) to assess portfolio risk under extreme market conditions.

## Project Status

**Current Phase**: Phase 2 - Core Simulation Engine ✅

## Features

### Phase 1: Data Ingestion and Preparation ✅
- Multi-source data connectors (Yahoo Finance, FRED API)
- Support for equities, bonds, commodities, and currencies
- Economic indicators integration
- Data validation and quality checks
- Data transformation pipeline (returns, volatility, technical indicators)
- PostgreSQL database with optimized schema

### Phase 2: Core Simulation Engine ✅
- Monte Carlo simulation using Geometric Brownian Motion
- Historical simulation with bootstrap resampling
- Correlation matrix calculation with Cholesky decomposition
- Multi-asset simulation with correlation support
- Value at Risk (VaR) and Conditional VaR (CVaR) calculation
- Scenario adjustment capabilities (shocks to returns, volatility, correlations)
- Comprehensive simulation statistics and analytics

## Architecture

```
cross-asset-simulator/
├── backend/
│   ├── config/              # Configuration and settings
│   ├── database/            # Database models and connection
│   ├── data_ingestion/      # Data connectors and ingestion
│   │   ├── connectors/      # YFinance, FRED connectors
│   │   ├── validators.py    # Data validation
│   │   ├── transformers.py  # Data transformation
│   │   └── ingestion_service.py
│   └── tests/               # Unit tests
├── requirements.txt
├── .env.example
└── init_database.py         # Database initialization script
```

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Git

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd -Cross-Asset-Stress-Scenario-Simulator
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `FRED_API_KEY`: (Optional) FRED API key for economic indicators
- `DATA_START_DATE`: Start date for historical data (default: 2019-01-01)
- `DATA_END_DATE`: End date for historical data (default: 2024-12-31)

### Get API Keys (Optional)

**FRED API** (for economic indicators):
1. Visit https://fred.stlouisfed.org/
2. Create a free account
3. Request an API key from https://fred.stlouisfed.org/docs/api/api_key.html
4. Add to `.env`: `FRED_API_KEY=your_key_here`

## Usage

### Initialize Database and Ingest Data

```bash
python init_database.py
```

This will:
1. Create database tables
2. Fetch historical data for predefined assets
3. Ingest economic indicators (if FRED API key is provided)
4. Store all data in PostgreSQL

### Asset Coverage

**Equities**: SPY, QQQ, DIA, IWM, AAPL, MSFT, GOOGL, AMZN  
**Bonds**: TLT, IEF, SHY, LQD, HYG  
**Commodities**: GLD, SLV, USO, DBA  
**Currencies**: EUR/USD, GBP/USD, JPY/USD, AUD/USD  

**Economic Indicators**: Federal Funds Rate, Treasury Yields, CPI, GDP, Unemployment, VIX, and more

### Run Tests

```bash
# Run all tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html

# Run specific test file
pytest backend/tests/test_validators.py -v
```

## Development

### Code Quality

```bash
# Format code
black backend/

# Lint code
ruff check backend/

# Type checking
mypy backend/
```

### Database Management

```python
from backend.database import db_manager

# Create tables
db_manager.create_tables()

# Drop tables (caution!)
db_manager.drop_tables()

# Get a session
with db_manager.get_session() as db:
    # Your database operations
    pass
```

## Technology Stack

- **Backend**: Python 3.11+, FastAPI
- **Database**: PostgreSQL 14+
- **Data Sources**: yfinance, FRED API
- **Data Processing**: Pandas, NumPy, SciPy
- **Testing**: pytest
- **Code Quality**: ruff, black, mypy

## Roadmap

- [x] **Phase 1**: Data Ingestion and Preparation
- [ ] **Phase 2**: Core Simulation Engine
- [ ] **Phase 3**: Scenario Definition and Management
- [ ] **Phase 4**: Results Analysis and Visualization
- [ ] **Phase 5**: Deployment and Integration

## Contributing

This is a phased implementation project. Each phase is completed and pushed to GitHub before proceeding to the next phase.

## License

MIT License

## Contact

For questions or issues, please open a GitHub issue.
