-- Recreate Minimal Database Tables for Simplified System
-- Run this to clean up and create only essential tables

-- First, truncate existing tables to clear data
TRUNCATE TABLE IF EXISTS iosapp.users CASCADE;
TRUNCATE TABLE IF EXISTS iosapp.saved_jobs CASCADE;
TRUNCATE TABLE IF EXISTS iosapp.job_views CASCADE;
TRUNCATE TABLE IF EXISTS iosapp.device_tokens CASCADE;

-- Drop and recreate tables with minimal schema
DROP TABLE IF EXISTS iosapp.users CASCADE;
DROP TABLE IF EXISTS iosapp.saved_jobs CASCADE;
DROP TABLE IF EXISTS iosapp.job_views CASCADE;
DROP TABLE IF EXISTS iosapp.device_tokens CASCADE;

-- Create minimal users table (simplified)
CREATE TABLE iosapp.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    keywords JSONB DEFAULT '[]'::jsonb,
    preferred_sources JSONB DEFAULT '[]'::jsonb,
    notifications_enabled BOOLEAN DEFAULT TRUE,
    last_notified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_users_device_id ON iosapp.users(device_id);
CREATE INDEX idx_users_email ON iosapp.users(email);

-- Create saved jobs table (minimal)
CREATE TABLE iosapp.saved_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    job_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, job_id)
);

-- Create job views table (minimal)
CREATE TABLE iosapp.job_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    job_id INTEGER NOT NULL,
    viewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create device tokens table (essential for push notifications)
CREATE TABLE iosapp.device_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) UNIQUE NOT NULL,
    device_token VARCHAR(500) NOT NULL,
    device_info JSONB DEFAULT '{}'::jsonb,
    user_id UUID,
    is_active BOOLEAN DEFAULT TRUE,
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for device tokens
CREATE INDEX idx_device_tokens_device_id ON iosapp.device_tokens(device_id);
CREATE INDEX idx_device_tokens_user_id ON iosapp.device_tokens(user_id);

-- Update trigger for users table
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON iosapp.users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_device_tokens_updated_at 
    BEFORE UPDATE ON iosapp.device_tokens 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (if needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA iosapp TO your_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA iosapp TO your_user;

-- Summary of created tables:
-- 1. users (9 fields) - Core user management
-- 2. saved_jobs (4 fields) - Job saving functionality  
-- 3. job_views (4 fields) - Basic analytics
-- 4. device_tokens (8 fields) - Push notifications

-- Total: 4 essential tables, ~25 fields (vs previous 40+ fields in users alone)