-- Create essential tables to support core app functionality
-- while keeping the minimal schema for notifications

-- Create users table (simplified)
CREATE TABLE IF NOT EXISTS iosapp.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255),
    device_id VARCHAR(255) UNIQUE,
    keywords JSONB DEFAULT '[]',
    notifications_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create device_tokens table (maps to device_users)
CREATE TABLE IF NOT EXISTS iosapp.device_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES iosapp.users(id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL,
    device_token VARCHAR(64) NOT NULL,
    device_info JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(device_token)
);

-- Create saved_jobs table for bookmarking
CREATE TABLE IF NOT EXISTS iosapp.saved_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES iosapp.users(id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL,
    job_title VARCHAR(500),
    job_company VARCHAR(200),
    job_source VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, job_id)
);

-- Create job_views table for analytics
CREATE TABLE IF NOT EXISTS iosapp.job_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES iosapp.users(id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL,
    job_title VARCHAR(500),
    job_company VARCHAR(200),
    job_source VARCHAR(100),
    view_duration_seconds INTEGER,
    viewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create job_notification_history for notification tracking
CREATE TABLE IF NOT EXISTS iosapp.job_notification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES iosapp.users(id) ON DELETE CASCADE,
    job_id INTEGER,
    job_title VARCHAR(500),
    job_company VARCHAR(200),
    job_source VARCHAR(100),
    job_unique_key VARCHAR(32) NOT NULL,
    matched_keywords JSONB,
    notification_sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_read BOOLEAN DEFAULT false,
    is_deleted BOOLEAN DEFAULT false,
    
    UNIQUE(user_id, job_unique_key)  -- Prevent duplicate notifications
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_device_id ON iosapp.users(device_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON iosapp.users(email);
CREATE INDEX IF NOT EXISTS idx_device_tokens_user_id ON iosapp.device_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_device_tokens_device_id ON iosapp.device_tokens(device_id);
CREATE INDEX IF NOT EXISTS idx_device_tokens_device_token ON iosapp.device_tokens(device_token);
CREATE INDEX IF NOT EXISTS idx_saved_jobs_user_id ON iosapp.saved_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_jobs_job_id ON iosapp.saved_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_job_views_user_id ON iosapp.job_views(user_id);
CREATE INDEX IF NOT EXISTS idx_job_views_job_id ON iosapp.job_views(job_id);
CREATE INDEX IF NOT EXISTS idx_job_notification_history_user_id ON iosapp.job_notification_history(user_id);
CREATE INDEX IF NOT EXISTS idx_job_notification_history_unique_key ON iosapp.job_notification_history(job_unique_key);

-- Insert existing device_users into new schema
INSERT INTO iosapp.users (device_id, keywords, notifications_enabled, created_at)
SELECT 
    device_token as device_id,
    keywords,
    notifications_enabled,
    created_at
FROM iosapp.device_users
ON CONFLICT (device_id) DO NOTHING;

-- Create device_tokens entries for existing devices
INSERT INTO iosapp.device_tokens (user_id, device_id, device_token, is_active, registered_at)
SELECT 
    u.id as user_id,
    u.device_id,
    u.device_id as device_token,
    u.notifications_enabled as is_active,
    u.created_at as registered_at
FROM iosapp.users u
LEFT JOIN iosapp.device_tokens dt ON u.id = dt.user_id
WHERE dt.id IS NULL;