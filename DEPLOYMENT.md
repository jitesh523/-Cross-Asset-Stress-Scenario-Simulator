# Deployment Guide

## Quick Start with Docker Compose

### Prerequisites
- Docker (v20.10+)
- Docker Compose (v2.0+)

### Steps

1. **Clone the repository**
```bash
git clone https://github.com/jitesh523/-Cross-Asset-Stress-Scenario-Simulator.git
cd -Cross-Asset-Stress-Scenario-Simulator
```

2. **Configure environment variables**
```bash
cp .env.production .env
# Edit .env with your API keys and configuration
nano .env
```

3. **Start the application**
```bash
docker-compose up -d
```

4. **Initialize the database**
```bash
# Wait for services to be healthy
docker-compose ps

# Run database initialization
docker-compose exec api python init_database.py
```

5. **Access the application**
- **Dashboard**: http://localhost
- **API Documentation**: http://localhost/docs
- **API Base**: http://localhost/api

### Service Ports
- Nginx (Frontend): 80
- API Server: 8000
- PostgreSQL: 5432

## Manual Deployment

### 1. Database Setup

```bash
# Install PostgreSQL with TimescaleDB
sudo apt-get install postgresql-15 postgresql-15-timescaledb

# Create database and user
sudo -u postgres psql
CREATE DATABASE simulator;
CREATE USER simulator_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE simulator TO simulator_user;
\q
```

### 2. Application Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://simulator_user:password@localhost:5432/simulator"
export FRED_API_KEY="your_key"

# Initialize database
python init_database.py

# Run API server
python run_api_server.py
```

### 3. Frontend Setup

```bash
# Serve frontend with any web server
# Example with Python's built-in server:
cd frontend
python -m http.server 3000
```

## Production Deployment

### Security Checklist

- [ ] Change all default passwords
- [ ] Generate strong SECRET_KEY
- [ ] Use HTTPS (configure SSL certificates)
- [ ] Restrict CORS origins in production
- [ ] Enable firewall rules
- [ ] Set up database backups
- [ ] Configure log rotation
- [ ] Use environment-specific .env files
- [ ] Enable API rate limiting
- [ ] Set up monitoring and alerts

### Environment Variables

Required:
- `DATABASE_URL`: PostgreSQL connection string
- `FRED_API_KEY`: FRED API key for economic data

Optional:
- `ALPHA_VANTAGE_API_KEY`: Alpha Vantage API key
- `DATA_START_DATE`: Start date for data ingestion
- `DATA_END_DATE`: End date for data ingestion
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Docker Commands

```bash
# Build and start services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Restart a specific service
docker-compose restart api

# Execute commands in container
docker-compose exec api python init_database.py
docker-compose exec postgres psql -U simulator_user -d simulator
```

### Scaling

To scale the API service:
```bash
docker-compose up -d --scale api=3
```

### Backup and Restore

**Backup database:**
```bash
docker-compose exec postgres pg_dump -U simulator_user simulator > backup.sql
```

**Restore database:**
```bash
docker-compose exec -T postgres psql -U simulator_user simulator < backup.sql
```

## Cloud Deployment

### AWS ECS

1. Build and push Docker image to ECR
2. Create ECS task definition
3. Set up RDS PostgreSQL instance
4. Configure ALB for load balancing
5. Deploy ECS service

### Google Cloud Run

1. Build container image
2. Push to Google Container Registry
3. Create Cloud SQL PostgreSQL instance
4. Deploy to Cloud Run with environment variables

### Azure Container Instances

1. Build and push to Azure Container Registry
2. Create Azure Database for PostgreSQL
3. Deploy container instance with environment variables

## Monitoring

### Health Checks

- API: `http://localhost:8000/health`
- Database: `docker-compose exec postgres pg_isready`

### Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs api
docker-compose logs postgres

# Follow logs in real-time
docker-compose logs -f api
```

### Metrics

Monitor:
- API response times
- Database connection pool
- Memory usage
- CPU usage
- Disk space

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U simulator_user -d simulator -c "SELECT 1;"
```

### API Not Responding

```bash
# Check API logs
docker-compose logs api

# Restart API service
docker-compose restart api

# Check if port is accessible
curl http://localhost:8000/health
```

### Frontend Not Loading

```bash
# Check Nginx logs
docker-compose logs nginx

# Verify frontend files
docker-compose exec nginx ls -la /usr/share/nginx/html

# Restart Nginx
docker-compose restart nginx
```

## Maintenance

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose up -d --build

# Run any new migrations
docker-compose exec api python init_database.py
```

### Database Maintenance

```bash
# Vacuum database
docker-compose exec postgres psql -U simulator_user -d simulator -c "VACUUM ANALYZE;"

# Check database size
docker-compose exec postgres psql -U simulator_user -d simulator -c "SELECT pg_size_pretty(pg_database_size('simulator'));"
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/jitesh523/-Cross-Asset-Stress-Scenario-Simulator/issues
- Documentation: README.md
