-- Create user profile tables for BirJob application
-- Run this script to create the necessary tables for user management

-- Users table - main user profiles
CREATE TABLE IF NOT EXISTS iosapp.users (
    id VARCHAR(255) PRIMARY KEY,
    device_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Personal Information
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    location VARCHAR(255),
    current_job_title VARCHAR(255),
    years_of_experience VARCHAR(50),
    linkedin_profile VARCHAR(500),
    portfolio_url VARCHAR(500),
    bio TEXT,
    
    -- Job Preferences (stored as JSON)
    desired_job_types JSON,
    remote_work_preference VARCHAR(50) DEFAULT 'Hybrid',
    skills JSON,
    preferred_locations JSON,
    min_salary INTEGER,
    max_salary INTEGER,
    salary_currency VARCHAR(10) DEFAULT 'USD',
    salary_negotiable BOOLEAN DEFAULT TRUE,
    
    -- Notification Settings
    job_matches_enabled BOOLEAN DEFAULT TRUE,
    application_reminders_enabled BOOLEAN DEFAULT TRUE,
    weekly_digest_enabled BOOLEAN DEFAULT FALSE,
    market_insights_enabled BOOLEAN DEFAULT TRUE,
    quiet_hours_enabled BOOLEAN DEFAULT TRUE,
    quiet_hours_start VARCHAR(5) DEFAULT '22:00',
    quiet_hours_end VARCHAR(5) DEFAULT '08:00',
    preferred_notification_time VARCHAR(5) DEFAULT '09:00',
    
    -- Privacy Settings
    profile_visibility VARCHAR(20) DEFAULT 'Public',
    share_analytics BOOLEAN DEFAULT TRUE,
    share_job_view_history BOOLEAN DEFAULT FALSE,
    allow_personalized_recommendations BOOLEAN DEFAULT TRUE,
    
    -- Profile Metadata
    profile_completeness INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on device_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_users_device_id ON iosapp.users(device_id);

-- Saved jobs table
CREATE TABLE IF NOT EXISTS iosapp.saved_jobs (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    job_id INTEGER NOT NULL,
    notes TEXT,
    application_status VARCHAR(20) DEFAULT 'not_applied',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
    UNIQUE (user_id, job_id)
);

-- Create indexes for saved jobs
CREATE INDEX IF NOT EXISTS idx_saved_jobs_user_id ON iosapp.saved_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_jobs_job_id ON iosapp.saved_jobs(job_id);

-- Job views tracking table
CREATE TABLE IF NOT EXISTS iosapp.job_views (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    job_id INTEGER NOT NULL,
    view_duration INTEGER, -- seconds
    source VARCHAR(50), -- 'job_list', 'recommendations', 'search'
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE
);

-- Create indexes for job views
CREATE INDEX IF NOT EXISTS idx_job_views_user_id ON iosapp.job_views(user_id);
CREATE INDEX IF NOT EXISTS idx_job_views_job_id ON iosapp.job_views(job_id);
CREATE INDEX IF NOT EXISTS idx_job_views_viewed_at ON iosapp.job_views(viewed_at);

-- Job applications tracking table
CREATE TABLE IF NOT EXISTS iosapp.job_applications (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    job_id INTEGER NOT NULL,
    
    -- Application details
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'interview', 'rejected', 'offer'
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    follow_up_date TIMESTAMP,
    
    -- Application source/method
    application_source VARCHAR(100), -- 'company_website', 'linkedin', 'indeed', etc.
    
    FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
    UNIQUE (user_id, job_id)
);

-- Create indexes for job applications
CREATE INDEX IF NOT EXISTS idx_job_applications_user_id ON iosapp.job_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_job_applications_job_id ON iosapp.job_applications(job_id);
CREATE INDEX IF NOT EXISTS idx_job_applications_status ON iosapp.job_applications(status);
CREATE INDEX IF NOT EXISTS idx_job_applications_applied_at ON iosapp.job_applications(applied_at);

-- User analytics table (computed insights)
CREATE TABLE IF NOT EXISTS iosapp.user_analytics (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    
    -- Profile insights
    profile_strength INTEGER DEFAULT 0,
    market_fit INTEGER DEFAULT 0,
    
    -- Job activity stats
    total_jobs_viewed INTEGER DEFAULT 0,
    total_jobs_saved INTEGER DEFAULT 0,
    total_applications INTEGER DEFAULT 0,
    average_view_time DECIMAL(10,2) DEFAULT 0,
    
    -- Matching insights
    total_matches INTEGER DEFAULT 0,
    average_match_score DECIMAL(5,2) DEFAULT 0,
    
    -- Computed insights (stored as JSON)
    improvement_areas JSON,
    most_viewed_categories JSON,
    top_matching_companies JSON,
    recommended_skills JSON,
    market_insights JSON,
    
    -- Timestamps
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE
);

-- Create index for user analytics
CREATE INDEX IF NOT EXISTS idx_user_analytics_user_id ON iosapp.user_analytics(user_id);

-- Add some constraints and checks (PostgreSQL syntax)
-- These will be added after table creation

-- Optional: Create a view for user profile summary
CREATE OR REPLACE VIEW iosapp.user_profile_summary AS
SELECT 
    u.id,
    u.device_id,
    u.first_name,
    u.last_name,
    u.email,
    u.current_job_title,
    u.profile_completeness,
    u.created_at,
    u.updated_at,
    COUNT(DISTINCT sj.id) as saved_jobs_count,
    COUNT(DISTINCT ja.id) as applications_count,
    COUNT(DISTINCT jv.id) as jobs_viewed_count
FROM iosapp.users u
LEFT JOIN iosapp.saved_jobs sj ON u.id = sj.user_id
LEFT JOIN iosapp.job_applications ja ON u.id = ja.user_id
LEFT JOIN iosapp.job_views jv ON u.id = jv.user_id
GROUP BY u.id, u.device_id, u.first_name, u.last_name, u.email, 
         u.current_job_title, u.profile_completeness, u.created_at, u.updated_at;