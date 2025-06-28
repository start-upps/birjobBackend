-- =====================================
-- User Tables Consolidation Migration
-- =====================================
-- Combines iosapp.users and iosapp.user_profiles into unified iosapp.users_unified
-- Keeps the best aspects of both: individual columns for core fields + JSONB for flexibility

-- Step 1: Create the unified users table
CREATE TABLE IF NOT EXISTS iosapp.users_unified (
    -- Primary identifiers
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Core personal information (individual columns for performance)
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(255),
    location VARCHAR(255),
    current_job_title VARCHAR(255),
    years_of_experience VARCHAR(255),
    linkedin_profile VARCHAR(255),
    portfolio_url VARCHAR(255),
    bio TEXT,
    
    -- Job preferences (individual columns for common queries)
    desired_job_types JSONB DEFAULT '[]'::jsonb,
    remote_work_preference VARCHAR(50) DEFAULT 'hybrid',
    skills JSONB DEFAULT '[]'::jsonb,
    preferred_locations JSONB DEFAULT '[]'::jsonb,
    
    -- Salary information
    min_salary INTEGER,
    max_salary INTEGER,
    salary_currency VARCHAR(10) DEFAULT 'USD',
    salary_negotiable BOOLEAN DEFAULT true,
    
    -- Keyword matching (new unified approach)
    match_keywords JSONB DEFAULT '[]'::jsonb,
    
    -- Notification settings (individual columns for performance)
    job_matches_enabled BOOLEAN DEFAULT true,
    application_reminders_enabled BOOLEAN DEFAULT true,
    weekly_digest_enabled BOOLEAN DEFAULT true,
    market_insights_enabled BOOLEAN DEFAULT false,
    quiet_hours_enabled BOOLEAN DEFAULT false,
    quiet_hours_start VARCHAR(10),
    quiet_hours_end VARCHAR(10),
    preferred_notification_time VARCHAR(10),
    
    -- Privacy settings (individual columns for security queries)
    profile_visibility VARCHAR(20) DEFAULT 'private',
    share_analytics BOOLEAN DEFAULT false,
    share_job_view_history BOOLEAN DEFAULT false,
    allow_personalized_recommendations BOOLEAN DEFAULT true,
    
    -- Additional flexible data (JSONB for extensibility)
    additional_personal_info JSONB DEFAULT '{}'::jsonb,
    additional_job_preferences JSONB DEFAULT '{}'::jsonb,
    additional_notification_settings JSONB DEFAULT '{}'::jsonb,
    additional_privacy_settings JSONB DEFAULT '{}'::jsonb,
    
    -- Metadata
    profile_completeness INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 2: Create performance indexes
CREATE INDEX IF NOT EXISTS idx_users_unified_device_id ON iosapp.users_unified (device_id);
CREATE INDEX IF NOT EXISTS idx_users_unified_email ON iosapp.users_unified (email);
CREATE INDEX IF NOT EXISTS idx_users_unified_location ON iosapp.users_unified (location);
CREATE INDEX IF NOT EXISTS idx_users_unified_job_title ON iosapp.users_unified (current_job_title);

-- GIN indexes for JSONB fields
CREATE INDEX IF NOT EXISTS idx_users_unified_match_keywords ON iosapp.users_unified USING GIN (match_keywords);
CREATE INDEX IF NOT EXISTS idx_users_unified_skills ON iosapp.users_unified USING GIN (skills);
CREATE INDEX IF NOT EXISTS idx_users_unified_desired_job_types ON iosapp.users_unified USING GIN (desired_job_types);
CREATE INDEX IF NOT EXISTS idx_users_unified_preferred_locations ON iosapp.users_unified USING GIN (preferred_locations);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_users_unified_bio_search ON iosapp.users_unified USING GIN (to_tsvector('english', bio));

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_users_unified_job_search ON iosapp.users_unified (current_job_title, location, years_of_experience);
CREATE INDEX IF NOT EXISTS idx_users_unified_notifications ON iosapp.users_unified (job_matches_enabled, application_reminders_enabled);

-- Step 3: Add table comments
COMMENT ON TABLE iosapp.users_unified IS 'Unified user table combining personal info, job preferences, notifications, and privacy settings';
COMMENT ON COLUMN iosapp.users_unified.match_keywords IS 'User-defined keywords for intelligent job matching';
COMMENT ON COLUMN iosapp.users_unified.additional_personal_info IS 'Flexible storage for additional personal information';
COMMENT ON COLUMN iosapp.users_unified.additional_job_preferences IS 'Flexible storage for additional job preferences';

-- Step 4: Create data migration function
CREATE OR REPLACE FUNCTION iosapp.migrate_user_data()
RETURNS TABLE(
    migrated_from_users INTEGER,
    migrated_from_profiles INTEGER,
    total_unified INTEGER
) AS $$
DECLARE
    users_count INTEGER := 0;
    profiles_count INTEGER := 0;
    unified_count INTEGER := 0;
BEGIN
    -- Migrate from iosapp.users table
    INSERT INTO iosapp.users_unified (
        device_id, first_name, last_name, email, phone, location,
        current_job_title, years_of_experience, linkedin_profile, portfolio_url, bio,
        desired_job_types, remote_work_preference, skills, preferred_locations,
        min_salary, max_salary, salary_currency, salary_negotiable,
        job_matches_enabled, application_reminders_enabled, weekly_digest_enabled, 
        market_insights_enabled, quiet_hours_enabled, quiet_hours_start, 
        quiet_hours_end, preferred_notification_time, profile_visibility,
        share_analytics, share_job_view_history, allow_personalized_recommendations,
        profile_completeness, created_at, updated_at
    )
    SELECT 
        device_id, first_name, last_name, email, phone, location,
        current_job_title, years_of_experience, linkedin_profile, portfolio_url, bio,
        COALESCE(desired_job_types, '[]'::jsonb),
        COALESCE(remote_work_preference, 'hybrid'),
        COALESCE(skills, '[]'::jsonb),
        COALESCE(preferred_locations, '[]'::jsonb),
        min_salary, max_salary, 
        COALESCE(salary_currency, 'USD'),
        COALESCE(salary_negotiable, true),
        COALESCE(job_matches_enabled, true),
        COALESCE(application_reminders_enabled, true),
        COALESCE(weekly_digest_enabled, true),
        COALESCE(market_insights_enabled, false),
        COALESCE(quiet_hours_enabled, false),
        quiet_hours_start, quiet_hours_end, preferred_notification_time,
        COALESCE(profile_visibility, 'private'),
        COALESCE(share_analytics, false),
        COALESCE(share_job_view_history, false),
        COALESCE(allow_personalized_recommendations, true),
        COALESCE(profile_completeness, 0),
        COALESCE(created_at, CURRENT_TIMESTAMP),
        COALESCE(updated_at, CURRENT_TIMESTAMP)
    FROM iosapp.users
    ON CONFLICT (device_id) DO NOTHING;
    
    GET DIAGNOSTICS users_count = ROW_COUNT;
    
    -- Update with data from iosapp.user_profiles (merge approach)
    UPDATE iosapp.users_unified 
    SET 
        match_keywords = COALESCE(p.match_keywords, '[]'::jsonb),
        additional_personal_info = COALESCE(p.personal_info, '{}'::jsonb),
        additional_job_preferences = COALESCE(p.job_preferences, '{}'::jsonb),
        additional_notification_settings = COALESCE(p.notification_settings, '{}'::jsonb),
        additional_privacy_settings = COALESCE(p.privacy_settings, '{}'::jsonb),
        updated_at = GREATEST(iosapp.users_unified.updated_at, COALESCE(p.last_updated, CURRENT_TIMESTAMP))
    FROM iosapp.user_profiles p
    WHERE iosapp.users_unified.device_id = p.device_id;
    
    GET DIAGNOSTICS profiles_count = ROW_COUNT;
    
    -- Insert profiles that don't exist in users table
    INSERT INTO iosapp.users_unified (
        device_id, match_keywords, additional_personal_info, 
        additional_job_preferences, additional_notification_settings,
        additional_privacy_settings, profile_completeness, created_at, updated_at
    )
    SELECT 
        p.device_id,
        COALESCE(p.match_keywords, '[]'::jsonb),
        COALESCE(p.personal_info, '{}'::jsonb),
        COALESCE(p.job_preferences, '{}'::jsonb),
        COALESCE(p.notification_settings, '{}'::jsonb),
        COALESCE(p.privacy_settings, '{}'::jsonb),
        COALESCE(p.profile_completeness, 0),
        COALESCE(p.created_at, CURRENT_TIMESTAMP),
        COALESCE(p.last_updated, CURRENT_TIMESTAMP)
    FROM iosapp.user_profiles p
    WHERE NOT EXISTS (
        SELECT 1 FROM iosapp.users_unified u 
        WHERE u.device_id = p.device_id
    );
    
    -- Get final count
    SELECT COUNT(*) INTO unified_count FROM iosapp.users_unified;
    
    RETURN QUERY SELECT users_count, profiles_count, unified_count;
END;
$$ LANGUAGE plpgsql;

-- Step 5: Create helper functions for the unified table
CREATE OR REPLACE FUNCTION iosapp.get_user_keywords(p_device_id VARCHAR)
RETURNS TEXT[] AS $$
BEGIN
    RETURN (
        SELECT ARRAY(
            SELECT jsonb_array_elements_text(match_keywords)
            FROM iosapp.users_unified 
            WHERE device_id = p_device_id
        )
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION iosapp.update_user_keywords(
    p_device_id VARCHAR,
    p_keywords TEXT[]
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE iosapp.users_unified 
    SET 
        match_keywords = to_jsonb(p_keywords),
        updated_at = CURRENT_TIMESTAMP
    WHERE device_id = p_device_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION iosapp.calculate_unified_profile_completeness(p_device_id VARCHAR)
RETURNS INTEGER AS $$
DECLARE
    completion_score INTEGER := 0;
    user_record RECORD;
BEGIN
    SELECT * INTO user_record FROM iosapp.users_unified WHERE device_id = p_device_id;
    
    IF NOT FOUND THEN
        RETURN 0;
    END IF;
    
    -- Core personal info (40 points max)
    IF user_record.first_name IS NOT NULL AND user_record.first_name != '' THEN completion_score := completion_score + 5; END IF;
    IF user_record.last_name IS NOT NULL AND user_record.last_name != '' THEN completion_score := completion_score + 5; END IF;
    IF user_record.email IS NOT NULL AND user_record.email != '' THEN completion_score := completion_score + 10; END IF;
    IF user_record.phone IS NOT NULL AND user_record.phone != '' THEN completion_score := completion_score + 5; END IF;
    IF user_record.location IS NOT NULL AND user_record.location != '' THEN completion_score := completion_score + 5; END IF;
    IF user_record.current_job_title IS NOT NULL AND user_record.current_job_title != '' THEN completion_score := completion_score + 5; END IF;
    IF user_record.bio IS NOT NULL AND user_record.bio != '' THEN completion_score := completion_score + 5; END IF;
    
    -- Job preferences (30 points max)
    IF jsonb_array_length(user_record.skills) > 0 THEN completion_score := completion_score + 10; END IF;
    IF jsonb_array_length(user_record.desired_job_types) > 0 THEN completion_score := completion_score + 5; END IF;
    IF jsonb_array_length(user_record.preferred_locations) > 0 THEN completion_score := completion_score + 5; END IF;
    IF user_record.min_salary IS NOT NULL THEN completion_score := completion_score + 5; END IF;
    IF user_record.max_salary IS NOT NULL THEN completion_score := completion_score + 5; END IF;
    
    -- Keyword matching (20 points max)
    IF jsonb_array_length(user_record.match_keywords) > 0 THEN completion_score := completion_score + 15; END IF;
    IF jsonb_array_length(user_record.match_keywords) >= 5 THEN completion_score := completion_score + 5; END IF;
    
    -- Additional info (10 points max)
    IF user_record.linkedin_profile IS NOT NULL AND user_record.linkedin_profile != '' THEN completion_score := completion_score + 5; END IF;
    IF user_record.portfolio_url IS NOT NULL AND user_record.portfolio_url != '' THEN completion_score := completion_score + 5; END IF;
    
    RETURN LEAST(completion_score, 100);
END;
$$ LANGUAGE plpgsql;

-- Step 6: Create trigger to auto-update profile completeness
CREATE OR REPLACE FUNCTION iosapp.update_profile_completeness_trigger()
RETURNS TRIGGER AS $$
BEGIN
    NEW.profile_completeness := iosapp.calculate_unified_profile_completeness(NEW.device_id);
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_profile_completeness
    BEFORE INSERT OR UPDATE ON iosapp.users_unified
    FOR EACH ROW
    EXECUTE FUNCTION iosapp.update_profile_completeness_trigger();

-- Step 7: Create views for backward compatibility (optional)
CREATE OR REPLACE VIEW iosapp.users_legacy_view AS
SELECT 
    id::varchar as id,
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
    min_salary,
    max_salary,
    salary_currency,
    salary_negotiable,
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
    created_at,
    updated_at
FROM iosapp.users_unified;