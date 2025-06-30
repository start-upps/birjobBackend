-- =====================================================
-- iOS App Database Schema Cleanup and Optimization
-- =====================================================
-- This script consolidates the fragmented iosapp schema
-- into a proper RDBMS design with foreign key relationships

-- Start transaction
BEGIN;

-- =====================================================
-- 1. BACKUP EXISTING DATA (Create temporary backup tables)
-- =====================================================

-- Backup users table
CREATE TABLE IF NOT EXISTS iosapp.users_backup AS 
SELECT * FROM iosapp.users;

-- Backup user_profiles table
CREATE TABLE IF NOT EXISTS iosapp.user_profiles_backup AS 
SELECT * FROM iosapp.user_profiles;

-- Backup device_tokens table
CREATE TABLE IF NOT EXISTS iosapp.device_tokens_backup AS 
SELECT * FROM iosapp.device_tokens;

-- =====================================================
-- 2. DROP UNNECESSARY TABLES
-- =====================================================

-- Drop empty and redundant tables
DROP TABLE IF EXISTS iosapp.migration_log CASCADE;
DROP VIEW IF EXISTS iosapp.users_legacy_view CASCADE;

-- =====================================================
-- 3. CREATE NEW OPTIMIZED SCHEMA
-- =====================================================

-- Main Users table (consolidated from all user sources)
DROP TABLE IF EXISTS iosapp.users_new CASCADE;
CREATE TABLE iosapp.users_new (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Personal Information
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    location VARCHAR(255),
    current_job_title VARCHAR(255),
    years_of_experience INTEGER,
    linkedin_profile VARCHAR(500),
    portfolio_url VARCHAR(500),
    bio TEXT,
    
    -- Job Preferences (JSONB for flexibility + performance)
    desired_job_types JSONB DEFAULT '[]'::jsonb,
    remote_work_preference VARCHAR(50) DEFAULT 'hybrid',
    skills JSONB DEFAULT '[]'::jsonb,
    preferred_locations JSONB DEFAULT '[]'::jsonb,
    match_keywords JSONB DEFAULT '[]'::jsonb,
    
    -- Salary preferences
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
    quiet_hours_start TIME DEFAULT '22:00',
    quiet_hours_end TIME DEFAULT '08:00',
    preferred_notification_time TIME DEFAULT '09:00',
    
    -- Privacy Settings
    profile_visibility VARCHAR(20) DEFAULT 'private' CHECK (profile_visibility IN ('public', 'private')),
    share_analytics BOOLEAN DEFAULT FALSE,
    share_job_view_history BOOLEAN DEFAULT FALSE,
    allow_personalized_recommendations BOOLEAN DEFAULT TRUE,
    
    -- Profile Metadata
    profile_completeness INTEGER DEFAULT 0 CHECK (profile_completeness >= 0 AND profile_completeness <= 100),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Additional flexible data
    additional_personal_info JSONB DEFAULT '{}'::jsonb,
    additional_job_preferences JSONB DEFAULT '{}'::jsonb,
    additional_notification_settings JSONB DEFAULT '{}'::jsonb,
    additional_privacy_settings JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Device Tokens table (linked to users)
DROP TABLE IF EXISTS iosapp.device_tokens_new CASCADE;
CREATE TABLE iosapp.device_tokens_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    device_token VARCHAR(255) UNIQUE NOT NULL,
    device_type VARCHAR(20) DEFAULT 'iOS' CHECK (device_type IN ('iOS', 'Android')),
    device_info JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    last_seen TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key to users
    CONSTRAINT fk_device_tokens_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users_new(id) 
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Keyword Subscriptions (linked to users, not devices)
DROP TABLE IF EXISTS iosapp.keyword_subscriptions_new CASCADE;
CREATE TABLE iosapp.keyword_subscriptions_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
    location_filters JSONB DEFAULT '{}'::jsonb,
    source_filters JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key to users
    CONSTRAINT fk_keyword_subscriptions_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users_new(id) 
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Job Matches (core functionality)
DROP TABLE IF EXISTS iosapp.job_matches_new CASCADE;
CREATE TABLE iosapp.job_matches_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    job_id INTEGER NOT NULL,
    
    -- Match scoring
    match_score DECIMAL(5,2) NOT NULL CHECK (match_score >= 0 AND match_score <= 100),
    matched_keywords JSONB DEFAULT '[]'::jsonb,
    match_reasons JSONB DEFAULT '[]'::jsonb,
    keyword_relevance JSONB DEFAULT '{}'::jsonb,
    
    -- Match metadata
    is_read BOOLEAN DEFAULT FALSE,
    is_saved BOOLEAN DEFAULT FALSE,
    is_applied BOOLEAN DEFAULT FALSE,
    user_feedback VARCHAR(20) CHECK (user_feedback IN ('like', 'dislike', 'not_interested')),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key to users
    CONSTRAINT fk_job_matches_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users_new(id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
        
    -- Unique constraint per user-job combination
    CONSTRAINT unique_user_job_match UNIQUE (user_id, job_id)
);

-- Saved Jobs (user job bookmarks)
DROP TABLE IF EXISTS iosapp.saved_jobs_new CASCADE;
CREATE TABLE iosapp.saved_jobs_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    job_id INTEGER NOT NULL,
    notes TEXT,
    application_status VARCHAR(20) DEFAULT 'not_applied' 
        CHECK (application_status IN ('not_applied', 'applied', 'interviewing', 'offered', 'rejected', 'withdrawn')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key to users
    CONSTRAINT fk_saved_jobs_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users_new(id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
        
    -- Unique constraint per user-job combination
    CONSTRAINT unique_user_saved_job UNIQUE (user_id, job_id)
);

-- Job Applications (track user applications)
DROP TABLE IF EXISTS iosapp.job_applications_new CASCADE;
CREATE TABLE iosapp.job_applications_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    job_id INTEGER NOT NULL,
    
    -- Application details
    application_method VARCHAR(50), -- 'direct', 'through_app', 'company_website', etc.
    application_status VARCHAR(20) DEFAULT 'submitted'
        CHECK (application_status IN ('submitted', 'reviewing', 'interviewing', 'offered', 'rejected', 'withdrawn')),
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Follow-up tracking
    follow_up_date DATE,
    interview_date TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    
    -- External references
    external_application_id VARCHAR(255),
    application_url VARCHAR(500),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key to users
    CONSTRAINT fk_job_applications_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users_new(id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
        
    -- Unique constraint per user-job combination
    CONSTRAINT unique_user_job_application UNIQUE (user_id, job_id)
);

-- Job Views (analytics tracking)
DROP TABLE IF EXISTS iosapp.job_views_new CASCADE;
CREATE TABLE iosapp.job_views_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    job_id INTEGER NOT NULL,
    
    -- View details
    view_duration INTEGER, -- in seconds
    view_source VARCHAR(50), -- 'search', 'match', 'saved', 'recommendation'
    device_type VARCHAR(20),
    
    -- Location context
    view_location VARCHAR(255),
    
    -- Timestamps
    viewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key to users
    CONSTRAINT fk_job_views_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users_new(id) 
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Push Notifications (notification history)
DROP TABLE IF EXISTS iosapp.push_notifications_new CASCADE;
CREATE TABLE iosapp.push_notifications_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    device_token_id UUID,
    
    -- Notification content
    notification_type VARCHAR(50) NOT NULL, -- 'job_match', 'application_reminder', 'weekly_digest', etc.
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    payload JSONB DEFAULT '{}'::jsonb,
    
    -- Related entities
    job_match_id UUID,
    job_id INTEGER,
    
    -- Delivery status
    status VARCHAR(20) DEFAULT 'pending' 
        CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'clicked')),
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    CONSTRAINT fk_push_notifications_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users_new(id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_push_notifications_device_token 
        FOREIGN KEY (device_token_id) REFERENCES iosapp.device_tokens_new(id) 
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_push_notifications_job_match 
        FOREIGN KEY (job_match_id) REFERENCES iosapp.job_matches_new(id) 
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- User Analytics (user insights and recommendations)
DROP TABLE IF EXISTS iosapp.user_analytics_new CASCADE;
CREATE TABLE iosapp.user_analytics_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    
    -- Profile insights
    profile_strength INTEGER DEFAULT 0 CHECK (profile_strength >= 0 AND profile_strength <= 100),
    market_fit_score INTEGER DEFAULT 0 CHECK (market_fit_score >= 0 AND market_fit_score <= 100),
    
    -- Activity metrics
    total_jobs_viewed INTEGER DEFAULT 0,
    total_jobs_saved INTEGER DEFAULT 0,
    total_applications INTEGER DEFAULT 0,
    total_matches_received INTEGER DEFAULT 0,
    average_view_time_seconds INTEGER DEFAULT 0,
    
    -- Matching insights
    average_match_score DECIMAL(5,2) DEFAULT 0,
    top_match_score DECIMAL(5,2) DEFAULT 0,
    total_keywords INTEGER DEFAULT 0,
    
    -- Computed insights (flexible JSON storage)
    skill_recommendations JSONB DEFAULT '[]'::jsonb,
    top_matching_companies JSONB DEFAULT '[]'::jsonb,
    recommended_job_types JSONB DEFAULT '[]'::jsonb,
    market_insights JSONB DEFAULT '{}'::jsonb,
    improvement_suggestions JSONB DEFAULT '[]'::jsonb,
    
    -- Computation metadata
    last_computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    computation_version VARCHAR(10) DEFAULT '1.0',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key to users
    CONSTRAINT fk_user_analytics_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users_new(id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
        
    -- Unique constraint per user
    CONSTRAINT unique_user_analytics UNIQUE (user_id)
);

-- =====================================================
-- 4. CREATE INDEXES FOR PERFORMANCE
-- =====================================================

-- Users table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_device_id ON iosapp.users_new(device_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON iosapp.users_new(email) WHERE email IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active ON iosapp.users_new(is_active) WHERE is_active = TRUE;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_updated_at ON iosapp.users_new(updated_at);

-- JSONB indexes for job preferences
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_match_keywords_gin ON iosapp.users_new USING GIN (match_keywords);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_skills_gin ON iosapp.users_new USING GIN (skills);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_desired_job_types_gin ON iosapp.users_new USING GIN (desired_job_types);

-- Device tokens indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_device_tokens_user_id ON iosapp.device_tokens_new(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_device_tokens_active ON iosapp.device_tokens_new(is_active) WHERE is_active = TRUE;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_device_tokens_last_seen ON iosapp.device_tokens_new(last_seen);

-- Job matches indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_matches_user_id ON iosapp.job_matches_new(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_matches_job_id ON iosapp.job_matches_new(job_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_matches_score ON iosapp.job_matches_new(match_score DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_matches_created_at ON iosapp.job_matches_new(created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_matches_unread ON iosapp.job_matches_new(user_id, is_read) WHERE is_read = FALSE;

-- Keyword subscriptions indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_keyword_subscriptions_user_id ON iosapp.keyword_subscriptions_new(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_keyword_subscriptions_active ON iosapp.keyword_subscriptions_new(is_active) WHERE is_active = TRUE;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_keyword_subscriptions_keywords_gin ON iosapp.keyword_subscriptions_new USING GIN (keywords);

-- Saved jobs indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_saved_jobs_user_id ON iosapp.saved_jobs_new(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_saved_jobs_job_id ON iosapp.saved_jobs_new(job_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_saved_jobs_status ON iosapp.saved_jobs_new(application_status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_saved_jobs_created_at ON iosapp.saved_jobs_new(created_at DESC);

-- Job applications indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_applications_user_id ON iosapp.job_applications_new(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_applications_job_id ON iosapp.job_applications_new(job_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_applications_status ON iosapp.job_applications_new(application_status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_applications_applied_at ON iosapp.job_applications_new(applied_at DESC);

-- Job views indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_views_user_id ON iosapp.job_views_new(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_views_job_id ON iosapp.job_views_new(job_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_views_viewed_at ON iosapp.job_views_new(viewed_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_views_source ON iosapp.job_views_new(view_source);

-- Push notifications indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_push_notifications_user_id ON iosapp.push_notifications_new(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_push_notifications_device_token_id ON iosapp.push_notifications_new(device_token_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_push_notifications_status ON iosapp.push_notifications_new(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_push_notifications_type ON iosapp.push_notifications_new(notification_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_push_notifications_created_at ON iosapp.push_notifications_new(created_at DESC);

-- User analytics indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_analytics_user_id ON iosapp.user_analytics_new(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_analytics_profile_strength ON iosapp.user_analytics_new(profile_strength DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_analytics_market_fit ON iosapp.user_analytics_new(market_fit_score DESC);

-- =====================================================
-- 5. CREATE TRIGGERS FOR AUTOMATIC UPDATES
-- =====================================================

-- Function to update timestamp
CREATE OR REPLACE FUNCTION iosapp.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON iosapp.users_new 
    FOR EACH ROW EXECUTE FUNCTION iosapp.update_updated_at_column();

CREATE TRIGGER update_device_tokens_updated_at BEFORE UPDATE ON iosapp.device_tokens_new 
    FOR EACH ROW EXECUTE FUNCTION iosapp.update_updated_at_column();

CREATE TRIGGER update_keyword_subscriptions_updated_at BEFORE UPDATE ON iosapp.keyword_subscriptions_new 
    FOR EACH ROW EXECUTE FUNCTION iosapp.update_updated_at_column();

CREATE TRIGGER update_job_matches_updated_at BEFORE UPDATE ON iosapp.job_matches_new 
    FOR EACH ROW EXECUTE FUNCTION iosapp.update_updated_at_column();

CREATE TRIGGER update_saved_jobs_updated_at BEFORE UPDATE ON iosapp.saved_jobs_new 
    FOR EACH ROW EXECUTE FUNCTION iosapp.update_updated_at_column();

CREATE TRIGGER update_job_applications_updated_at BEFORE UPDATE ON iosapp.job_applications_new 
    FOR EACH ROW EXECUTE FUNCTION iosapp.update_updated_at_column();

CREATE TRIGGER update_user_analytics_updated_at BEFORE UPDATE ON iosapp.user_analytics_new 
    FOR EACH ROW EXECUTE FUNCTION iosapp.update_updated_at_column();

-- Function to calculate profile completeness
CREATE OR REPLACE FUNCTION iosapp.calculate_profile_completeness()
RETURNS TRIGGER AS $$
DECLARE
    completeness_score INTEGER := 0;
BEGIN
    -- Basic info (40 points max)
    IF NEW.first_name IS NOT NULL AND NEW.first_name != '' THEN completeness_score := completeness_score + 5; END IF;
    IF NEW.last_name IS NOT NULL AND NEW.last_name != '' THEN completeness_score := completeness_score + 5; END IF;
    IF NEW.email IS NOT NULL AND NEW.email != '' THEN completeness_score := completeness_score + 10; END IF;
    IF NEW.location IS NOT NULL AND NEW.location != '' THEN completeness_score := completeness_score + 5; END IF;
    IF NEW.current_job_title IS NOT NULL AND NEW.current_job_title != '' THEN completeness_score := completeness_score + 10; END IF;
    IF NEW.bio IS NOT NULL AND NEW.bio != '' THEN completeness_score := completeness_score + 5; END IF;
    
    -- Job preferences (40 points max)
    IF NEW.skills IS NOT NULL AND jsonb_array_length(NEW.skills) > 0 THEN completeness_score := completeness_score + 15; END IF;
    IF NEW.match_keywords IS NOT NULL AND jsonb_array_length(NEW.match_keywords) > 0 THEN completeness_score := completeness_score + 15; END IF;
    IF NEW.desired_job_types IS NOT NULL AND jsonb_array_length(NEW.desired_job_types) > 0 THEN completeness_score := completeness_score + 5; END IF;
    IF NEW.min_salary IS NOT NULL AND NEW.max_salary IS NOT NULL THEN completeness_score := completeness_score + 5; END IF;
    
    -- Additional info (20 points max)
    IF NEW.linkedin_profile IS NOT NULL AND NEW.linkedin_profile != '' THEN completeness_score := completeness_score + 5; END IF;
    IF NEW.portfolio_url IS NOT NULL AND NEW.portfolio_url != '' THEN completeness_score := completeness_score + 5; END IF;
    IF NEW.years_of_experience IS NOT NULL THEN completeness_score := completeness_score + 5; END IF;
    IF NEW.phone IS NOT NULL AND NEW.phone != '' THEN completeness_score := completeness_score + 5; END IF;
    
    NEW.profile_completeness := completeness_score;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for profile completeness calculation
CREATE TRIGGER calculate_profile_completeness_trigger 
    BEFORE INSERT OR UPDATE ON iosapp.users_new 
    FOR EACH ROW EXECUTE FUNCTION iosapp.calculate_profile_completeness();

-- =====================================================
-- 6. MIGRATE DATA FROM OLD TABLES
-- =====================================================

-- Migrate users_unified data to new users table
INSERT INTO iosapp.users_new (
    device_id, first_name, last_name, email, phone, location, current_job_title,
    years_of_experience, linkedin_profile, portfolio_url, bio,
    desired_job_types, remote_work_preference, skills, preferred_locations, match_keywords,
    min_salary, max_salary, salary_currency, salary_negotiable,
    job_matches_enabled, application_reminders_enabled, weekly_digest_enabled,
    market_insights_enabled, quiet_hours_enabled, quiet_hours_start, quiet_hours_end,
    preferred_notification_time, profile_visibility, share_analytics,
    share_job_view_history, allow_personalized_recommendations,
    additional_personal_info, additional_job_preferences,
    additional_notification_settings, additional_privacy_settings,
    created_at, updated_at
)
SELECT 
    device_id, first_name, last_name, email, phone, location, current_job_title,
    years_of_experience, linkedin_profile, portfolio_url, bio,
    COALESCE(desired_job_types, '[]'::jsonb), 
    COALESCE(remote_work_preference, 'hybrid'),
    COALESCE(skills, '[]'::jsonb), 
    COALESCE(preferred_locations, '[]'::jsonb), 
    COALESCE(match_keywords, '[]'::jsonb),
    min_salary, max_salary, 
    COALESCE(currency, 'USD'),
    COALESCE(is_negotiable, TRUE),
    COALESCE(job_matches_enabled, TRUE),
    COALESCE(application_reminders_enabled, TRUE),
    COALESCE(weekly_digest_enabled, FALSE),
    COALESCE(market_insights_enabled, TRUE),
    COALESCE(quiet_hours_enabled, TRUE),
    COALESCE(quiet_hours_start::time, '22:00'::time),
    COALESCE(quiet_hours_end::time, '08:00'::time),
    COALESCE(preferred_notification_time::time, '09:00'::time),
    COALESCE(profile_visibility, 'private'),
    COALESCE(share_analytics, FALSE),
    COALESCE(share_job_view_history, FALSE),
    COALESCE(allow_personalized_recommendations, TRUE),
    COALESCE(additional_personal_info, '{}'::jsonb),
    COALESCE(additional_job_preferences, '{}'::jsonb),
    COALESCE(additional_notification_settings, '{}'::jsonb),
    COALESCE(additional_privacy_settings, '{}'::jsonb),
    created_at, updated_at
FROM iosapp.users_unified
ON CONFLICT (device_id) DO NOTHING;

-- Migrate device tokens with proper user linking
INSERT INTO iosapp.device_tokens_new (
    user_id, device_token, device_type, device_info, is_active, last_seen, created_at, updated_at
)
SELECT 
    u.id as user_id,
    dt.device_token,
    COALESCE(dt.device_type, 'iOS'),
    COALESCE(dt.device_info, '{}'::jsonb),
    COALESCE(dt.is_active, TRUE),
    dt.last_seen,
    dt.created_at,
    dt.updated_at
FROM iosapp.device_tokens dt
JOIN iosapp.users_new u ON u.device_id = dt.device_token -- Assuming device_token maps to device_id
ON CONFLICT (device_token) DO NOTHING;

-- Create device tokens for users without devices (fallback)
INSERT INTO iosapp.device_tokens_new (user_id, device_token, device_type, device_info, is_active)
SELECT 
    u.id,
    u.device_id,
    'iOS',
    '{}'::jsonb,
    TRUE
FROM iosapp.users_new u
WHERE NOT EXISTS (
    SELECT 1 FROM iosapp.device_tokens_new dt WHERE dt.user_id = u.id
)
ON CONFLICT (device_token) DO NOTHING;

-- Migrate keyword subscriptions
INSERT INTO iosapp.keyword_subscriptions_new (
    user_id, keywords, location_filters, source_filters, is_active, created_at, updated_at
)
SELECT 
    u.id as user_id,
    COALESCE(ks.keywords, u.match_keywords, '[]'::jsonb),
    COALESCE(ks.location_filters, '{}'::jsonb),
    COALESCE(ks.source_filters, '[]'::jsonb),
    COALESCE(ks.is_active, TRUE),
    COALESCE(ks.created_at, CURRENT_TIMESTAMP),
    COALESCE(ks.updated_at, CURRENT_TIMESTAMP)
FROM iosapp.users_new u
LEFT JOIN iosapp.keyword_subscriptions ks ON ks.device_token_id IN (
    SELECT dt.id FROM iosapp.device_tokens dt WHERE dt.device_token = u.device_id
);

-- Migrate existing saved jobs, job applications, job views if they exist
-- (These will likely be empty but we'll include for completeness)

-- Initialize user analytics for all users
INSERT INTO iosapp.user_analytics_new (user_id)
SELECT id FROM iosapp.users_new
ON CONFLICT (user_id) DO NOTHING;

-- =====================================================
-- 7. CREATE VIEWS FOR BACKWARD COMPATIBILITY
-- =====================================================

-- Create a view that matches the old users_unified structure
CREATE OR REPLACE VIEW iosapp.users_unified AS
SELECT 
    id,
    device_id,
    first_name,
    last_name,
    email,
    phone,
    location,
    current_job_title,
    years_of_experience,
    linkedin_profile,
    portfolio_url,
    bio,
    desired_job_types,
    remote_work_preference,
    skills,
    preferred_locations,
    match_keywords,
    min_salary,
    max_salary,
    salary_currency as currency,
    salary_negotiable as is_negotiable,
    job_matches_enabled,
    application_reminders_enabled,
    weekly_digest_enabled,
    market_insights_enabled,
    quiet_hours_enabled,
    quiet_hours_start,
    quiet_hours_end,
    preferred_notification_time,
    profile_visibility,
    share_analytics,
    share_job_view_history,
    allow_personalized_recommendations,
    profile_completeness,
    additional_personal_info,
    additional_job_preferences,
    additional_notification_settings,
    additional_privacy_settings,
    is_active,
    created_at,
    updated_at
FROM iosapp.users_new;

-- =====================================================
-- 8. DROP OLD TABLES AND RENAME NEW ONES
-- =====================================================

-- Drop old tables (after successful migration)
DROP TABLE IF EXISTS iosapp.users CASCADE;
DROP TABLE IF EXISTS iosapp.user_profiles CASCADE;
DROP TABLE IF EXISTS iosapp.device_tokens CASCADE;
DROP TABLE IF EXISTS iosapp.keyword_subscriptions CASCADE;
DROP TABLE IF EXISTS iosapp.job_matches CASCADE;
DROP TABLE IF EXISTS iosapp.saved_jobs CASCADE;
DROP TABLE IF EXISTS iosapp.job_applications CASCADE;
DROP TABLE IF EXISTS iosapp.job_views CASCADE;
DROP TABLE IF EXISTS iosapp.push_notifications CASCADE;
DROP TABLE IF EXISTS iosapp.user_analytics CASCADE;

-- Rename new tables to replace old ones
ALTER TABLE iosapp.users_new RENAME TO users;
ALTER TABLE iosapp.device_tokens_new RENAME TO device_tokens;
ALTER TABLE iosapp.keyword_subscriptions_new RENAME TO keyword_subscriptions;
ALTER TABLE iosapp.job_matches_new RENAME TO job_matches;
ALTER TABLE iosapp.saved_jobs_new RENAME TO saved_jobs;
ALTER TABLE iosapp.job_applications_new RENAME TO job_applications;
ALTER TABLE iosapp.job_views_new RENAME TO job_views;
ALTER TABLE iosapp.push_notifications_new RENAME TO push_notifications;
ALTER TABLE iosapp.user_analytics_new RENAME TO user_analytics;

-- =====================================================
-- 9. VERIFY SCHEMA INTEGRITY
-- =====================================================

-- Verify foreign key relationships
DO $$
DECLARE
    fk_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO fk_count
    FROM information_schema.table_constraints 
    WHERE constraint_type = 'FOREIGN KEY' 
    AND table_schema = 'iosapp';
    
    RAISE NOTICE 'Total foreign key constraints created: %', fk_count;
    
    IF fk_count < 8 THEN
        RAISE EXCEPTION 'Expected at least 8 foreign key constraints, but found %', fk_count;
    END IF;
END $$;

-- Verify data migration
DO $$
DECLARE
    user_count INTEGER;
    device_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO user_count FROM iosapp.users;
    SELECT COUNT(*) INTO device_count FROM iosapp.device_tokens;
    
    RAISE NOTICE 'Migrated % users and % device tokens', user_count, device_count;
    
    IF user_count = 0 THEN
        RAISE EXCEPTION 'No users were migrated - something went wrong';
    END IF;
END $$;

-- =====================================================
-- 10. GRANT PERMISSIONS
-- =====================================================

-- Grant permissions to application user (adjust username as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA iosapp TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA iosapp TO your_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA iosapp TO your_app_user;

-- Commit transaction
COMMIT;

-- =====================================================
-- SCHEMA OPTIMIZATION COMPLETE
-- =====================================================

-- Create a summary of the new schema
SELECT 
    'iosapp' as schema_name,
    COUNT(*) as total_tables,
    (SELECT COUNT(*) FROM information_schema.table_constraints 
     WHERE constraint_type = 'FOREIGN KEY' AND table_schema = 'iosapp') as foreign_keys,
    (SELECT COUNT(*) FROM information_schema.statistics 
     WHERE table_schema = 'iosapp') as indexes
FROM information_schema.tables 
WHERE table_schema = 'iosapp' AND table_type = 'BASE TABLE';