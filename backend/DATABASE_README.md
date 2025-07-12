# StackIt Database Setup Guide

## Prerequisites

Before setting up the database, ensure you have:

1. **PostgreSQL 12+** installed and running
2. **Python 3.8+** with pip
3. **Git** for version control

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Database Setup

Create a PostgreSQL database and user:

```sql
-- Connect to PostgreSQL as superuser
CREATE DATABASE stackit_db;
CREATE USER stackit WITH PASSWORD 'stackit';
GRANT ALL PRIVILEGES ON DATABASE stackit_db TO stackit;
```

### 3. Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your database credentials:

```env
DATABASE_URL=postgresql://stackit:stackit@localhost:5432/stackit_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=stackit_db
DB_USER=stackit
DB_PASSWORD=stackit
SECRET_KEY=your-secret-key-here
```

### 4. Database Initialization

Run the database management script to set up everything:

```bash
# Check database connection
python manage_db.py check-connection

# Create tables using SQLAlchemy
python manage_db.py create-tables

# Or use Alembic migrations (recommended for production)
python manage_db.py generate-migration -m "Initial migration"
python manage_db.py migrate

# Seed with initial data
python manage_db.py seed-data

# Set up performance optimizations
python manage_db.py setup-optimizations
```

## Database Management Commands

The `manage_db.py` script provides various database management commands:

### Basic Operations

```bash
# Check database connection
python manage_db.py check-connection

# Show database configuration
python manage_db.py info

# Create all tables
python manage_db.py create-tables

# Drop all tables (⚠️ DESTRUCTIVE)
python manage_db.py drop-tables
```

### Migration Management

```bash
# Generate a new migration
python manage_db.py generate-migration -m "Add new feature"

# Apply migrations
python manage_db.py migrate

# Rollback last migration
python manage_db.py downgrade

# Show current migration
python manage_db.py current

# Show migration history
python manage_db.py history
```

### Data Management

```bash
# Seed database with initial data
python manage_db.py seed-data

# Set up database optimizations
python manage_db.py setup-optimizations
```

## Database Schema

### Core Tables

1. **users** - User accounts and profiles
2. **questions** - User questions with rich text
3. **answers** - Answers to questions
4. **tags** - Content categorization
5. **question_tags** - Many-to-many relationship
6. **votes** - User voting on answers
7. **comments** - Comments on answers
8. **notifications** - Real-time notifications

### Key Relationships

- Users can ask multiple questions (1:N)
- Questions can have multiple answers (1:N)
- Questions can have multiple tags (M:N via question_tags)
- Users can vote on answers (M:N via votes)
- Answers can have multiple comments (1:N)
- Users receive notifications (1:N)

## Performance Features

### Indexing

The database includes comprehensive indexing for:
- Foreign key relationships
- Common query patterns
- Full-text search capabilities
- User and content statistics

### PostgreSQL Extensions

The setup automatically creates these extensions:
- `pg_trgm` - Trigram similarity search
- `btree_gin` - GIN indexes on btree types
- `unaccent` - Accent-insensitive search

### Database Functions

Custom PostgreSQL functions for:
- Updating question statistics
- Calculating user reputation
- Full-text search with ranking

### Triggers

Automatic triggers for:
- Question statistics updates
- User reputation calculations
- Data consistency maintenance

## Development Workflow

### Making Schema Changes

1. **Modify Models**: Update SQLAlchemy models in `app/models/`
2. **Generate Migration**: `python manage_db.py generate-migration -m "Description"`
3. **Review Migration**: Check the generated migration file
4. **Apply Migration**: `python manage_db.py migrate`
5. **Test Changes**: Verify the changes work as expected

### Adding Seed Data

1. **Edit Seed Script**: Modify `app/seed_data.py`
2. **Run Seeding**: `python manage_db.py seed-data`
3. **Verify Data**: Check that data was created correctly

### Performance Tuning

1. **Monitor Queries**: Use PostgreSQL's `pg_stat_statements`
2. **Add Indexes**: Update models with new indexes
3. **Update Functions**: Modify `app/database_optimizations.py`
4. **Apply Changes**: `python manage_db.py setup-optimizations`

## Production Deployment

### Database Configuration

For production, ensure:

1. **Connection Pooling**: Configure appropriate pool sizes
2. **SSL Connections**: Enable SSL for security
3. **Backup Strategy**: Set up automated backups
4. **Monitoring**: Configure performance monitoring

### Environment Variables

Set production environment variables:

```env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@prod-host:5432/stackit_prod
SECRET_KEY=secure-random-key
```

### Migration Deployment

For zero-downtime deployments:

1. **Backward Compatible**: Ensure migrations are backward compatible
2. **Staged Rollout**: Deploy migrations before application code
3. **Rollback Plan**: Have rollback procedures ready
4. **Monitoring**: Monitor performance after deployment

## Troubleshooting

### Common Issues

**Connection Errors**:
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection settings
python manage_db.py check-connection
```

**Migration Errors**:
```bash
# Check current migration status
python manage_db.py current

# Reset migrations (⚠️ DESTRUCTIVE)
python manage_db.py downgrade base
python manage_db.py migrate
```

**Performance Issues**:
```bash
# Check database statistics
SELECT * FROM pg_stat_user_tables;

# Analyze query performance
EXPLAIN ANALYZE SELECT ...;
```

### Logging

Enable SQL query logging for debugging:

```python
# In app/config.py
debug = True  # This enables SQL query logging
```

### Database Maintenance

Regular maintenance tasks:

```sql
-- Update table statistics
ANALYZE;

-- Rebuild indexes if needed
REINDEX DATABASE stackit_db;

-- Check for unused indexes
SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;
```

## Testing

### Test Database Setup

For testing, use a separate database:

```bash
# Create test database
createdb stackit_test

# Set test environment
export DATABASE_URL=postgresql://stackit:stackit@localhost:5432/stackit_test

# Run migrations
python manage_db.py migrate
```

### Integration Tests

Run database integration tests:

```bash
# Run tests with test database
pytest tests/test_database.py -v
```

## Backup and Recovery

### Backup

```bash
# Full database backup
pg_dump stackit_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Schema only backup
pg_dump --schema-only stackit_db > schema_backup.sql
```

### Recovery

```bash
# Restore from backup
psql stackit_db < backup_file.sql

# Restore schema only
psql stackit_db < schema_backup.sql
```

## Monitoring

### Key Metrics

Monitor these database metrics:
- Connection count and pool usage
- Query execution times
- Index usage statistics
- Table sizes and growth
- Lock contention

### Useful Queries

```sql
-- Active connections
SELECT * FROM pg_stat_activity;

-- Slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC;

-- Index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch 
FROM pg_stat_user_indexes;
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the database design documentation
3. Check PostgreSQL logs for errors
4. Consult the FastAPI and SQLAlchemy documentation
