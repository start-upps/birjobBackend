-- Proper RDBMS Schema with Foreign Key Relationships
-- This schema follows database normalization principles

-- Drop existing tables in proper order (child tables first)
DROP TABLE IF EXISTS iosapp.job_views CASCADE;
DROP TABLE IF EXISTS iosapp.saved_jobs CASCADE;
DROP TABLE IF EXISTS iosapp.device_tokens CASCADE;
DROP TABLE IF EXISTS iosapp.users CASCADE;

-- Create users table (parent table)
CREATE TABLE iosapp.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,                        -- Email should be unique if provided
    keywords JSONB DEFAULT '[]'::jsonb,              -- Job search keywords array
    preferred_sources JSONB DEFAULT '[]'::jsonb,     -- Preferred job sources array
    notifications_enabled BOOLEAN DEFAULT TRUE,       -- Push notification preference
    last_notified_at TIMESTAMP WITH TIME ZONE,       -- Last notification timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' OR email IS NULL),
    CONSTRAINT users_keywords_type CHECK (jsonb_typeof(keywords) = 'array'),
    CONSTRAINT users_sources_type CHECK (jsonb_typeof(preferred_sources) = 'array')
);

-- Create device_tokens table (child of users)
CREATE TABLE iosapp.device_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                           -- FOREIGN KEY to users.id
    device_id VARCHAR(255) UNIQUE NOT NULL,          -- Unique device identifier
    device_token VARCHAR(500) NOT NULL,              -- APNS device token
    device_info JSONB DEFAULT '{}'::jsonb,          -- Device metadata (OS, app version)
    is_active BOOLEAN DEFAULT TRUE,                  -- Token validity status
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_device_tokens_user FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
    
    -- Check Constraints
    CONSTRAINT device_token_length CHECK (length(device_token) >= 64),
    CONSTRAINT device_info_type CHECK (jsonb_typeof(device_info) = 'object')
);

-- Create saved_jobs table (child of users)
CREATE TABLE iosapp.saved_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                           -- FOREIGN KEY to users.id
    job_id INTEGER NOT NULL,                         -- External job system ID
    job_title VARCHAR(500),                          -- Cache job title for performance
    job_company VARCHAR(255),                        -- Cache job company for performance
    job_source VARCHAR(100),                         -- Cache job source for performance
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_saved_jobs_user FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
    
    -- Unique Constraints
    CONSTRAINT unique_user_job UNIQUE(user_id, job_id),
    
    -- Check Constraints
    CONSTRAINT positive_job_id CHECK (job_id > 0)
);

-- Create job_views table (child of users)
CREATE TABLE iosapp.job_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                           -- FOREIGN KEY to users.id
    job_id INTEGER NOT NULL,                         -- External job system ID
    job_title VARCHAR(500),                          -- Cache job title for analytics
    job_company VARCHAR(255),                        -- Cache job company for analytics
    job_source VARCHAR(100),                         -- Cache job source for analytics
    view_duration_seconds INTEGER DEFAULT 0,         -- How long user viewed job
    viewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_job_views_user FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
    
    -- Check Constraints
    CONSTRAINT positive_job_id CHECK (job_id > 0),
    CONSTRAINT non_negative_duration CHECK (view_duration_seconds >= 0)
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON iosapp.users(email) WHERE email IS NOT NULL;
CREATE INDEX idx_users_created_at ON iosapp.users(created_at);

CREATE INDEX idx_device_tokens_device_id ON iosapp.device_tokens(device_id);
CREATE INDEX idx_device_tokens_user_id ON iosapp.device_tokens(user_id);
CREATE INDEX idx_device_tokens_active ON iosapp.device_tokens(is_active) WHERE is_active = true;

CREATE INDEX idx_saved_jobs_user_id ON iosapp.saved_jobs(user_id);
CREATE INDEX idx_saved_jobs_job_id ON iosapp.saved_jobs(job_id);
CREATE INDEX idx_saved_jobs_created_at ON iosapp.saved_jobs(created_at);
CREATE INDEX idx_saved_jobs_source ON iosapp.saved_jobs(job_source);

CREATE INDEX idx_job_views_user_id ON iosapp.job_views(user_id);
CREATE INDEX idx_job_views_job_id ON iosapp.job_views(job_id);
CREATE INDEX idx_job_views_viewed_at ON iosapp.job_views(viewed_at);
CREATE INDEX idx_job_views_source ON iosapp.job_views(job_source);

-- Create update triggers for timestamps
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

-- Create views for common queries
CREATE VIEW iosapp.active_users AS
SELECT 
    u.id,
    u.email,
    u.keywords,
    u.preferred_sources,
    u.notifications_enabled,
    u.created_at,
    COUNT(dt.id) as device_count,
    COUNT(sj.id) as saved_jobs_count,
    COUNT(jv.id) as total_job_views,
    MAX(jv.viewed_at) as last_activity
FROM iosapp.users u
LEFT JOIN iosapp.device_tokens dt ON u.id = dt.user_id AND dt.is_active = true
LEFT JOIN iosapp.saved_jobs sj ON u.id = sj.user_id
LEFT JOIN iosapp.job_views jv ON u.id = jv.user_id
GROUP BY u.id, u.email, u.keywords, u.preferred_sources, u.notifications_enabled, u.created_at;

CREATE VIEW iosapp.user_analytics AS
SELECT 
    u.id as user_id,
    u.email,
    u.created_at as user_since,
    EXTRACT(days FROM (CURRENT_TIMESTAMP - u.created_at)) as account_age_days,
    COUNT(DISTINCT dt.id) as active_devices,
    COUNT(DISTINCT sj.id) as total_saved_jobs,
    COUNT(DISTINCT jv.id) as total_job_views,
    COUNT(DISTINCT jv.job_id) as unique_jobs_viewed,
    COALESCE(AVG(jv.view_duration_seconds), 0) as avg_view_duration,
    MAX(jv.viewed_at) as last_activity,
    jsonb_array_length(u.keywords) as keywords_count,
    jsonb_array_length(u.preferred_sources) as preferred_sources_count
FROM iosapp.users u
LEFT JOIN iosapp.device_tokens dt ON u.id = dt.user_id AND dt.is_active = true
LEFT JOIN iosapp.saved_jobs sj ON u.id = sj.user_id
LEFT JOIN iosapp.job_views jv ON u.id = jv.user_id
GROUP BY u.id, u.email, u.created_at, u.keywords, u.preferred_sources;

-- Grant permissions (uncomment if needed for specific database users)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA iosapp TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA iosapp TO your_app_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA iosapp TO your_readonly_user;

-- Insert sample data for testing (optional)
-- INSERT INTO iosapp.users (email, keywords, preferred_sources) VALUES 
-- ('test@example.com', '["python", "django"]', '["linkedin", "indeed"]'),
-- ('user2@example.com', '["javascript", "react"]', '["glassdoor"]');

-- Summary of changes:
-- 1. Proper foreign key relationships between all tables
-- 2. Cascading deletes to maintain referential integrity
-- 3. Check constraints for data validation
-- 4. Unique constraints to prevent duplicates
-- 5. Proper indexes for query performance
-- 6. Views for common analytics queries
-- 7. Additional fields for better caching and analytics
-- 8. Email uniqueness constraint
-- 9. Removed device_id from users table (now only in device_tokens)
-- 10. Better data types and constraints