# StackIt FastAPI Setup Guide

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Git

### 1. Clone and Setup

```bash
git clone <repository-url>
cd StackIt-odoo/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Option 1: Automated setup (recommended)
python setup_database.py

# Option 2: Manual setup
cp .env.example .env
# Edit .env with your database settings
python manage_db.py create-tables
python manage_db.py seed-data
```

### 3. Run the Application

```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the Python module
python -m uvicorn app.main:app --reload
```

### 4. Access the API

- API Base URL: http://localhost:8000/api/v1
- Interactive Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Detailed Setup

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/stackit_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=stackit_db
DB_USER=username
DB_PASSWORD=password

# Application Configuration
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development

# Cache Configuration
CACHE_DIR=./cache

# Notification Configuration
NOTIFICATION_CHANNEL=stackit_notifications
```

### Database Management

The application includes a comprehensive database management CLI:

```bash
# Check database connection
python manage_db.py check-connection

# Show database information
python manage_db.py info

# Create tables
python manage_db.py create-tables

# Seed with initial data
python manage_db.py seed-data

# Set up performance optimizations
python manage_db.py setup-optimizations

# Migration commands
python manage_db.py generate-migration -m "Description"
python manage_db.py migrate
python manage_db.py downgrade
python manage_db.py current
python manage_db.py history
```

### Docker Setup (Alternative)

```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Wait for database to be ready, then run migrations
python manage_db.py migrate
python manage_db.py seed-data

# Optional: Start pgAdmin for database management
docker-compose --profile admin up -d pgadmin
```

### Testing

```bash
# Run database tests
python test_database.py

# Run manual tests only
python test_database.py --manual

# Run pytest tests only
python test_database.py --pytest
```

## Development Workflow

### 1. Making Database Changes

```bash
# 1. Modify SQLAlchemy models in app/models/
# 2. Generate migration
python manage_db.py generate-migration -m "Add new feature"
# 3. Review the generated migration file
# 4. Apply migration
python manage_db.py migrate
# 5. Test changes
python test_database.py
```

### 2. Adding New API Endpoints

1. **Create Pydantic schemas** in `app/schemas/`
2. **Add business logic** in `app/api/v1/`
3. **Update router registration** in `app/main.py`
4. **Test endpoints** using `/docs` or API client
5. **Add tests** for new functionality

### 3. Code Quality

```bash
# Linting with Ruff
ruff check .
ruff format .

# Type checking (if mypy is installed)
mypy app/
```

## Production Deployment

### 1. Environment Setup

```env
# Production environment variables
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=secure-random-key-256-bits
DATABASE_URL=postgresql://user:pass@prod-host:5432/stackit_prod

# Security settings
CORS_ORIGINS=["https://yourdomain.com"]
```

### 2. Database Preparation

```bash
# Run migrations
python manage_db.py migrate

# Set up optimizations
python manage_db.py setup-optimizations

# Seed production data (if needed)
python manage_db.py seed-data
```

### 3. Application Server

#### Using Gunicorn

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### 4. Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. Process Management (Systemd)

```ini
# /etc/systemd/system/stackit-api.service
[Unit]
Description=StackIt FastAPI Application
After=network.target

[Service]
Type=exec
User=stackit
Group=stackit
WorkingDirectory=/opt/stackit/backend
Environment=PATH=/opt/stackit/backend/venv/bin
ExecStart=/opt/stackit/backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable stackit-api
sudo systemctl start stackit-api
sudo systemctl status stackit-api
```

## Monitoring and Logging

### 1. Application Logs

Logs are written to:
- Console output
- `logs/stackit.log` (general logs)
- `logs/stackit_errors.log` (error logs)

### 2. Health Monitoring

```bash
# Health check endpoint
curl http://localhost:8000/health

# Database connection check
python manage_db.py check-connection
```

### 3. Performance Monitoring

The application includes built-in performance logging:
- Slow query detection
- API endpoint performance
- Authentication attempts
- Security events

## Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
python manage_db.py check-connection

# Check environment variables
python manage_db.py info
```

#### Migration Errors

```bash
# Check current migration status
python manage_db.py current

# Reset migrations (⚠️ DESTRUCTIVE)
python manage_db.py downgrade base
python manage_db.py migrate
```

#### Import Errors

```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Verify virtual environment
which python
pip list
```

### Performance Issues

```bash
# Check database performance
python manage_db.py setup-optimizations

# Monitor slow queries in PostgreSQL logs
tail -f /var/log/postgresql/postgresql-*.log | grep "slow query"

# Check API performance in application logs
tail -f logs/stackit.log | grep "API"
```

### Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use HTTPS in production
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable database SSL
- [ ] Regular security updates
- [ ] Monitor authentication logs
- [ ] Backup database regularly

## Backup and Recovery

### Database Backup

```bash
# Full backup
pg_dump stackit_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/opt/backups/stackit"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump stackit_db | gzip > "$BACKUP_DIR/stackit_$DATE.sql.gz"
find "$BACKUP_DIR" -name "stackit_*.sql.gz" -mtime +7 -delete
```

### Recovery

```bash
# Restore from backup
psql stackit_db < backup_file.sql

# Or from compressed backup
gunzip -c backup_file.sql.gz | psql stackit_db
```

## Support and Resources

- **API Documentation**: `/docs` endpoint
- **Database Schema**: `DATABASE_DESIGN.md`
- **Database Setup**: `DATABASE_README.md`
- **Project Overview**: `DATABASE_SUMMARY.md`
- **Health Check**: `/health` endpoint

For issues or questions:
1. Check the troubleshooting section
2. Review application logs
3. Consult the API documentation
4. Check PostgreSQL logs for database issues
