-- StackIt Database Initialization Script
-- This script runs when the PostgreSQL container starts for the first time

-- Create required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Enable pg_stat_statements for query monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Set up database configuration for better performance
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET log_min_duration_statement = 1000;
ALTER SYSTEM SET log_checkpoints = on;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_lock_waits = on;

-- Optimize for development (adjust for production)
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Create a function to reload configuration
CREATE OR REPLACE FUNCTION reload_config()
RETURNS void AS $$
BEGIN
    PERFORM pg_reload_conf();
    RAISE NOTICE 'Configuration reloaded successfully';
END;
$$ LANGUAGE plpgsql;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'StackIt database initialized successfully';
    RAISE NOTICE 'Extensions created: pg_trgm, btree_gin, unaccent, pg_stat_statements';
    RAISE NOTICE 'Performance settings optimized for development';
    RAISE NOTICE 'Use SELECT reload_config(); to reload configuration after changes';
END;
$$;
