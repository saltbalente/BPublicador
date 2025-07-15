-- EBPublicador Database Initialization Script
-- This script sets up the initial database configuration for PostgreSQL

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Set timezone
SET timezone = 'UTC';

-- Create custom types
DO $$ 
BEGIN
    -- Post status enum
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'post_status') THEN
        CREATE TYPE post_status AS ENUM ('draft', 'published', 'archived');
    END IF;
    
    -- Content type enum
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'content_type') THEN
        CREATE TYPE content_type AS ENUM ('blog_post', 'article', 'social_post', 'email', 'landing_page');
    END IF;
    
    -- AI provider enum
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ai_provider') THEN
        CREATE TYPE ai_provider AS ENUM ('openai', 'gemini', 'fallback');
    END IF;
END $$;

-- Create indexes for better performance (will be created by SQLAlchemy, but good to have)
-- These will be created automatically by the application, but we can prepare some custom ones

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function for full-text search (will be used later)
CREATE OR REPLACE FUNCTION create_search_vector(title TEXT, content TEXT, tags TEXT[])
RETURNS tsvector AS $$
BEGIN
    RETURN to_tsvector('english', 
        COALESCE(title, '') || ' ' || 
        COALESCE(content, '') || ' ' || 
        COALESCE(array_to_string(tags, ' '), '')
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE ebpublicador TO ebpublicador;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ebpublicador;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ebpublicador;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO ebpublicador;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ebpublicador;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ebpublicador;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO ebpublicador;

-- Optimize PostgreSQL settings for the application
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Create a simple health check function
CREATE OR REPLACE FUNCTION health_check()
RETURNS TABLE(status TEXT, timestamp TIMESTAMP) AS $$
BEGIN
    RETURN QUERY SELECT 'healthy'::TEXT, CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'EBPublicador database initialized successfully at %', CURRENT_TIMESTAMP;
END $$;