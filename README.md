# Cross-Asset Stress Scenario Simulator

A comprehensive tool for simulating stress scenarios across multiple asset classes (equities, bonds, commodities, currencies) to assess portfolio risk under extreme market conditions.

## Features

### Data Ingestion
- Multi-source data connectors (Yahoo Finance, FRED API)
- Support for equities, bonds, commodities, and currencies
- Economic indicators integration
- Data validation, quality checks, and transformation pipeline
- PostgreSQL database with optimized schema

### Simulation Engine
- Monte Carlo simulation using Geometric Brownian Motion
- Regime-aware Monte Carlo with dynamic correlation adjustments
- Historical simulation with bootstrap resampling
- Correlation matrix calculation with Cholesky decomposition
- Multi-asset simulation with correlation support

### Risk Analytics
- Value at Risk (VaR) and Conditional VaR / Expected Shortfall (CVaR)
- Portfolio optimization via Mean-Variance Optimization (MVO)
- Tactical hedging recommendations with trade suggestions
- Scenario adjustment capabilities (shocks to returns, volatility, correlations)

### Stress Scenarios
- Predefined scenarios based on historical events:
  - 2008 Financial Crisis
  - COVID-19 Market Crash (March 2020)
  - Interest Rate Shock (+200 bps)
  - Oil Price Shock (+100%)
  - Volatility Spike
  - Currency Crisis
- AI-powered scenario generation from natural language (OpenAI / Anthropic)
- Scenario CRUD operations, versioning, and tagging

### API & Dashboard
- FastAPI REST API with full Swagger/OpenAPI docs
- Modern React dashboard (Vite + Tailwind CSS + Recharts)
- Real-time analytics and system health monitoring
- Export functionality (JSON, CSV)

### Deployment
- Docker containerization with multi-stage builds
- Docker Compose orchestration (API, PostgreSQL, Nginx)
- GitHub Actions CI/CD pipeline
- Production-ready configuration with health checks

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
│   ├── scenarios/           # Scenario definitions and AI engine
│   ├── simulation/          # Monte Carlo, historical sim, optimizer
│   ├── api/                 # FastAPI routes and middleware
│   └── tests/               # Unit tests
├── frontend/                # React dashboard
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── requirements.txt
└── init_database.py
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

### API Keys (Optional)

**FRED API** (for economic indicators):
1. Visit https://fred.stlouisfed.org/
2. Create a free account
3. Request an API key from https://fred.stlouisfed.org/docs/api/api_key.html
4. Add to `.env`: `FRED_API_KEY=your_key_here`

## Usage

### Initialize Database

```bash
python init_database.py
```

### Run the API Server

```bash
python run_api_server.py
```

- **API Base**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **React Dashboard**: Run `npm run dev` in `frontend/` → http://localhost:5173

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/simulations/run` | Run simulations |
| POST | `/api/simulations/optimize` | Portfolio optimization |
| GET | `/api/scenarios/` | List scenarios |
| POST | `/api/scenarios/generate-ai` | AI scenario generation |
| POST | `/api/scenarios/{id}/run` | Run a scenario |
| GET | `/api/analysis/results` | Get results |
| GET | `/api/analysis/summary` | System summary |

### Docker Deployment

```bash
# Configure environment
cp .env.production .env

# Start all services
docker-compose up -d

# Initialize database
docker-compose exec api python init_database.py

# Access: http://localhost (Dashboard) | http://localhost/docs (API)
```

### Asset Coverage

**Equities**: SPY, QQQ, DIA, IWM, AAPL, MSFT, GOOGL, AMZN
**Bonds**: TLT, IEF, SHY, LQD, HYG
**Commodities**: GLD, SLV, USO, DBA
**Currencies**: EUR/USD, GBP/USD, JPY/USD, AUD/USD
**Economic Indicators**: Fed Funds Rate, Treasury Yields, CPI, GDP, Unemployment, VIX

### Run Tests

```bash
pytest backend/tests/ -v

# With coverage
pytest backend/tests/ --cov=backend --cov-report=html
```

## Development

### Code Quality

```bash
black backend/        # Format
flake8 backend/       # Lint
isort backend/        # Sort imports
mypy backend/         # Type checking
```

### Database Management

```python
from backend.database import get_db_manager

db_manager = get_db_manager()
db_manager.create_tables()

with db_manager.get_session() as db:
    # your database operations
    pass
```

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **Frontend**: React, Vite, Tailwind CSS, Recharts
- **Database**: PostgreSQL 14+
- **Data**: yfinance, FRED API, Pandas, NumPy, SciPy
- **AI**: OpenAI / Anthropic (optional, for scenario generation)
- **Deployment**: Docker, Nginx, GitHub Actions
- **Testing**: pytest, flake8, black, isort

## License

MIT License
