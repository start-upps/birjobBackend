-- =====================================================
-- Clean Rebuild of iOS App Database Schema
-- =====================================================
-- This script completely removes all existing data and 
-- recreates the schema with proper RDBMS design

-- =====================================================
-- 1. DROP ALL EXISTING TABLES AND DATA
-- =====================================================

-- Drop all tables in cascade mode to remove dependencies
DROP TABLE IF EXISTS iosapp.users_backup CASCADE;
DROP TABLE IF EXISTS iosapp.user_profiles_backup CASCADE;
DROP TABLE IF EXISTS iosapp.device_tokens_backup CASCADE;
DROP TABLE IF EXISTS iosapp.users_unified CASCADE;
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
DROP TABLE IF EXISTS iosapp.processed_jobs CASCADE;
DROP TABLE IF EXISTS iosapp.migration_log CASCADE;

-- Drop any existing views
DROP VIEW IF EXISTS iosapp.users_legacy_view CASCADE;

-- Drop functions if they exist
DROP FUNCTION IF EXISTS iosapp.update_updated_at_column() CASCADE;
DROP FUNCTION IF EXISTS iosapp.calculate_profile_completeness() CASCADE;
DROP FUNCTION IF EXISTS iosapp.update_profile_completeness_trigger() CASCADE;

-- =====================================================
-- 2. CREATE MAIN USERS TABLE (PRIMARY)
-- =====================================================

CREATE TABLE iosapp.users (
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

-- =====================================================
-- 3. CREATE DEVICE TOKENS TABLE (LINKED TO USERS)
-- =====================================================

CREATE TABLE iosapp.device_tokens (
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
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- =====================================================
-- 4. CREATE KEYWORD SUBSCRIPTIONS TABLE
-- =====================================================

CREATE TABLE iosapp.keyword_subscriptions (
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
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- =====================================================
-- 5. CREATE JOB MATCHES TABLE
-- =====================================================

CREATE TABLE iosapp.job_matches (
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
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
        
    -- Unique constraint per user-job combination
    CONSTRAINT unique_user_job_match UNIQUE (user_id, job_id)
);

-- =====================================================
-- 6. CREATE SAVED JOBS TABLE
-- =====================================================

CREATE TABLE iosapp.saved_jobs (
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
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
        
    -- Unique constraint per user-job combination
    CONSTRAINT unique_user_saved_job UNIQUE (user_id, job_id)
);

-- =====================================================
-- 7. CREATE JOB APPLICATIONS TABLE
-- =====================================================

CREATE TABLE iosapp.job_applications (
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
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
        
    -- Unique constraint per user-job combination
    CONSTRAINT unique_user_job_application UNIQUE (user_id, job_id)
);

-- =====================================================
-- 8. CREATE JOB VIEWS TABLE
-- =====================================================

CREATE TABLE iosapp.job_views (
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
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- =====================================================
-- 9. CREATE PUSH NOTIFICATIONS TABLE
-- =====================================================

CREATE TABLE iosapp.push_notifications (
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
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_push_notifications_device_token 
        FOREIGN KEY (device_token_id) REFERENCES iosapp.device_tokens(id) 
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_push_notifications_job_match 
        FOREIGN KEY (job_match_id) REFERENCES iosapp.job_matches(id) 
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- =====================================================
-- 10. CREATE USER ANALYTICS TABLE
-- =====================================================

CREATE TABLE iosapp.user_analytics (
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
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
        
    -- Unique constraint per user
    CONSTRAINT unique_user_analytics UNIQUE (user_id)
);

-- =====================================================
-- 11. CREATE FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update timestamp
CREATE OR REPLACE FUNCTION iosapp.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

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

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON iosapp.users 
    FOR EACH ROW EXECUTE FUNCTION iosapp.update_updated_at_column();

CREATE TRIGGER update_device_tokens_updated_at BEFORE UPDATE ON iosapp.device_tokens 
    FOR EACH ROW EXECUTE FUNCTION iosapp.update_updated_at_column();

CREATE TRIGGER update_keyword_subscriptions_updated_at BEFORE UPDATE ON iosapp.keyword_subscriptions 
    FOR EACH ROW EXECUTE FUNCTION iosapp.update_updated_at_column();

CREATE TRIGGER update_job_matches_updated_at BEFORE UPDATE ON iosapp.job_matches 
    FOR EACH ROW EXECUTE FUNCTION iosapp.update_updated_at_column();

CREATE TRIGGER update_saved_jobs_updated_at BEFORE UPDATE ON iosapp.saved_jobs 
    FOR EACH ROW EXECUTE FUNCTION iosapp.update_updated_at_column();

CREATE TRIGGER update_job_applications_updated_at BEFORE UPDATE ON iosapp.job_applications 
    FOR EACH ROW EXECUTE FUNCTION iosapp.update_updated_at_column();

CREATE TRIGGER update_user_analytics_updated_at BEFORE UPDATE ON iosapp.user_analytics 
    FOR EACH ROW EXECUTE FUNCTION iosapp.update_updated_at_column();

-- Trigger for profile completeness calculation
CREATE TRIGGER calculate_profile_completeness_trigger 
    BEFORE INSERT OR UPDATE ON iosapp.users 
    FOR EACH ROW EXECUTE FUNCTION iosapp.calculate_profile_completeness();

-- =====================================================
-- 12. CREATE BACKWARD COMPATIBILITY VIEW
-- =====================================================

-- Create a view that matches the old users_unified structure for API compatibility
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
FROM iosapp.users;

-- =====================================================
-- 13. FINAL VERIFICATION
-- =====================================================

-- Verify schema integrity
DO $$
DECLARE
    fk_count INTEGER;
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO fk_count
    FROM information_schema.table_constraints 
    WHERE constraint_type = 'FOREIGN KEY' 
    AND table_schema = 'iosapp';
    
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables 
    WHERE table_schema = 'iosapp' AND table_type = 'BASE TABLE';
    
    RAISE NOTICE 'Schema rebuild complete:';
    RAISE NOTICE '- % tables created', table_count;
    RAISE NOTICE '- % foreign key constraints created', fk_count;
    RAISE NOTICE '- All data has been cleared';
    RAISE NOTICE '- Ready for fresh data import';
END $$;

-- Show final schema summary
SELECT 
    'iosapp' as schema_name,
    COUNT(*) as total_tables,
    (SELECT COUNT(*) FROM information_schema.table_constraints 
     WHERE constraint_type = 'FOREIGN KEY' AND table_schema = 'iosapp') as foreign_keys
FROM information_schema.tables 
WHERE table_schema = 'iosapp' AND table_type = 'BASE TABLE';