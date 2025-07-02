-- Recreate Analytics Schema with Proper RDBMS Relationships
-- This completely recreates the analytics tables with proper foreign key connections

-- STEP 1: Drop all existing analytics tables (CASCADE to handle dependencies)
-- =========================================================================

DROP TABLE IF EXISTS iosapp.notification_analytics CASCADE;
DROP TABLE IF EXISTS iosapp.user_preferences_history CASCADE;
DROP TABLE IF EXISTS iosapp.job_engagement CASCADE;
DROP TABLE IF EXISTS iosapp.search_analytics CASCADE;
DROP TABLE IF EXISTS iosapp.user_actions CASCADE;
DROP TABLE IF EXISTS iosapp.user_sessions CASCADE;

-- Drop materialized views if they exist
DROP MATERIALIZED VIEW IF EXISTS iosapp.daily_user_stats CASCADE;
DROP MATERIALIZED VIEW IF EXISTS iosapp.user_engagement_summary CASCADE;
DROP MATERIALIZED VIEW IF EXISTS iosapp.session_analytics_comprehensive CASCADE;

-- STEP 2: Create user_sessions table (foundation for all analytics)
-- ================================================================

CREATE TABLE iosapp.user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    session_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    app_version VARCHAR(20),
    os_version VARCHAR(20),
    actions_count INTEGER DEFAULT 0,
    jobs_viewed_count INTEGER DEFAULT 0,
    jobs_saved_count INTEGER DEFAULT 0,
    searches_performed INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_user_sessions_user FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
    
    -- Check Constraints
    CONSTRAINT session_duration_positive CHECK (duration_seconds >= 0),
    CONSTRAINT session_end_after_start CHECK (session_end >= session_start OR session_end IS NULL),
    CONSTRAINT actions_count_positive CHECK (actions_count >= 0)
);

-- STEP 3: Create search_analytics table (with session relationship)
-- ================================================================

CREATE TABLE iosapp.search_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id UUID,                                 -- NEW: Foreign key to user_sessions
    search_query VARCHAR(500) NOT NULL,
    normalized_query VARCHAR(500),
    results_count INTEGER DEFAULT 0,
    clicked_results INTEGER DEFAULT 0,
    time_to_first_click INTEGER,
    total_session_time INTEGER DEFAULT 0,
    filters_applied JSONB DEFAULT '{}'::jsonb,
    result_job_ids JSONB DEFAULT '[]'::jsonb,
    clicked_job_ids JSONB DEFAULT '[]'::jsonb,
    search_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_search_analytics_user FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
    CONSTRAINT fk_search_analytics_session FOREIGN KEY (session_id) REFERENCES iosapp.user_sessions(id) ON DELETE SET NULL,
    
    -- Check Constraints
    CONSTRAINT results_count_positive CHECK (results_count >= 0),
    CONSTRAINT clicked_results_reasonable CHECK (clicked_results <= results_count),
    CONSTRAINT search_query_not_empty CHECK (length(search_query) > 0)
);

-- STEP 4: Create user_actions table (with job, session, and search relationships)
-- ===============================================================================

CREATE TABLE iosapp.user_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id UUID,                                 -- Foreign key to user_sessions
    job_id INTEGER,                                  -- Foreign key to jobs_jobpost
    search_id UUID,                                  -- NEW: Foreign key to search_analytics
    action_type VARCHAR(50) NOT NULL,
    action_details JSONB DEFAULT '{}'::jsonb,
    search_query VARCHAR(500),
    page_url VARCHAR(500),
    duration_seconds INTEGER DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_user_actions_user FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_actions_session FOREIGN KEY (session_id) REFERENCES iosapp.user_sessions(id) ON DELETE SET NULL,
    CONSTRAINT fk_user_actions_job FOREIGN KEY (job_id) REFERENCES scraper.jobs_jobpost(id) ON DELETE SET NULL,
    CONSTRAINT fk_user_actions_search FOREIGN KEY (search_id) REFERENCES iosapp.search_analytics(id) ON DELETE SET NULL,
    
    -- Check Constraints
    CONSTRAINT action_duration_positive CHECK (duration_seconds >= 0),
    CONSTRAINT action_type_not_empty CHECK (length(action_type) > 0)
);

-- STEP 5: Create job_engagement table (with job and session relationships)
-- ========================================================================

CREATE TABLE iosapp.job_engagement (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id UUID,                                 -- NEW: Foreign key to user_sessions
    job_id INTEGER NOT NULL,                         -- Foreign key to jobs_jobpost
    job_title VARCHAR(500),
    job_company VARCHAR(255),
    job_source VARCHAR(100),
    job_location VARCHAR(255),
    
    -- Engagement metrics
    total_view_time INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    first_viewed_at TIMESTAMP WITH TIME ZONE,
    last_viewed_at TIMESTAMP WITH TIME ZONE,
    
    -- User actions
    is_saved BOOLEAN DEFAULT FALSE,
    saved_at TIMESTAMP WITH TIME ZONE,
    unsaved_at TIMESTAMP WITH TIME ZONE,
    
    -- Application tracking
    applied BOOLEAN DEFAULT FALSE,
    applied_at TIMESTAMP WITH TIME ZONE,
    application_source VARCHAR(100),
    
    -- Engagement scoring
    engagement_score INTEGER DEFAULT 0,
    last_calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_job_engagement_user FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
    CONSTRAINT fk_job_engagement_session FOREIGN KEY (session_id) REFERENCES iosapp.user_sessions(id) ON DELETE SET NULL,
    CONSTRAINT fk_job_engagement_job FOREIGN KEY (job_id) REFERENCES scraper.jobs_jobpost(id) ON DELETE CASCADE,
    
    -- Unique Constraints
    CONSTRAINT unique_user_job_engagement UNIQUE(user_id, job_id),
    
    -- Check Constraints
    CONSTRAINT view_time_positive CHECK (total_view_time >= 0),
    CONSTRAINT view_count_positive CHECK (view_count >= 0),
    CONSTRAINT engagement_score_range CHECK (engagement_score >= 0 AND engagement_score <= 100),
    CONSTRAINT last_viewed_after_first CHECK (last_viewed_at >= first_viewed_at OR last_viewed_at IS NULL)
);

-- STEP 6: Create user_preferences_history table
-- =============================================

CREATE TABLE iosapp.user_preferences_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    change_type VARCHAR(50) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    change_reason VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_user_preferences_history_user FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
    
    -- Check Constraints
    CONSTRAINT change_type_not_empty CHECK (length(change_type) > 0)
);

-- STEP 7: Create notification_analytics table (with job, device, and job_engagement relationships)
-- ================================================================================================

CREATE TABLE iosapp.notification_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    device_token_id UUID,                            -- Foreign key to device_tokens
    job_id INTEGER,                                  -- Foreign key to jobs_jobpost
    job_engagement_id UUID,                          -- NEW: Foreign key to job_engagement
    notification_type VARCHAR(50) NOT NULL,
    notification_title VARCHAR(200),
    notification_body TEXT,
    
    -- Delivery tracking
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    
    -- Status tracking
    delivery_status VARCHAR(20) DEFAULT 'sent',
    error_message TEXT,
    
    -- Engagement tracking
    led_to_app_open BOOLEAN DEFAULT FALSE,
    led_to_job_view BOOLEAN DEFAULT FALSE,
    led_to_job_save BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_notification_analytics_user FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
    CONSTRAINT fk_notification_analytics_device FOREIGN KEY (device_token_id) REFERENCES iosapp.device_tokens(id) ON DELETE SET NULL,
    CONSTRAINT fk_notification_analytics_job FOREIGN KEY (job_id) REFERENCES scraper.jobs_jobpost(id) ON DELETE SET NULL,
    CONSTRAINT fk_notification_analytics_job_engagement FOREIGN KEY (job_engagement_id) REFERENCES iosapp.job_engagement(id) ON DELETE SET NULL,
    
    -- Check Constraints
    CONSTRAINT notification_type_not_empty CHECK (length(notification_type) > 0),
    CONSTRAINT delivery_status_valid CHECK (delivery_status IN ('sent', 'delivered', 'failed', 'pending'))
);

-- STEP 8: Create comprehensive indexes for performance
-- ===================================================

-- User sessions indexes
CREATE INDEX idx_user_sessions_user_id ON iosapp.user_sessions(user_id);
CREATE INDEX idx_user_sessions_start_time ON iosapp.user_sessions(session_start);
CREATE INDEX idx_user_sessions_device_id ON iosapp.user_sessions(device_id);

-- User actions indexes
CREATE INDEX idx_user_actions_user_id ON iosapp.user_actions(user_id);
CREATE INDEX idx_user_actions_session_id ON iosapp.user_actions(session_id);
CREATE INDEX idx_user_actions_type ON iosapp.user_actions(action_type);
CREATE INDEX idx_user_actions_timestamp ON iosapp.user_actions(timestamp);
CREATE INDEX idx_user_actions_job_id ON iosapp.user_actions(job_id) WHERE job_id IS NOT NULL;
CREATE INDEX idx_user_actions_search_id ON iosapp.user_actions(search_id) WHERE search_id IS NOT NULL;

-- Search analytics indexes
CREATE INDEX idx_search_analytics_user_id ON iosapp.search_analytics(user_id);
CREATE INDEX idx_search_analytics_session_id ON iosapp.search_analytics(session_id);
CREATE INDEX idx_search_analytics_query ON iosapp.search_analytics(search_query);
CREATE INDEX idx_search_analytics_timestamp ON iosapp.search_analytics(search_timestamp);

-- Job engagement indexes
CREATE INDEX idx_job_engagement_user_id ON iosapp.job_engagement(user_id);
CREATE INDEX idx_job_engagement_session_id ON iosapp.job_engagement(session_id);
CREATE INDEX idx_job_engagement_job_id ON iosapp.job_engagement(job_id);
CREATE INDEX idx_job_engagement_last_viewed ON iosapp.job_engagement(last_viewed_at);
CREATE INDEX idx_job_engagement_engagement_score ON iosapp.job_engagement(engagement_score);

-- User preferences history indexes
CREATE INDEX idx_user_preferences_history_user_id ON iosapp.user_preferences_history(user_id);
CREATE INDEX idx_user_preferences_history_changed_at ON iosapp.user_preferences_history(changed_at);
CREATE INDEX idx_user_preferences_history_change_type ON iosapp.user_preferences_history(change_type);

-- Notification analytics indexes
CREATE INDEX idx_notification_analytics_user_id ON iosapp.notification_analytics(user_id);
CREATE INDEX idx_notification_analytics_device_token_id ON iosapp.notification_analytics(device_token_id);
CREATE INDEX idx_notification_analytics_job_id ON iosapp.notification_analytics(job_id) WHERE job_id IS NOT NULL;
CREATE INDEX idx_notification_analytics_job_engagement_id ON iosapp.notification_analytics(job_engagement_id) WHERE job_engagement_id IS NOT NULL;
CREATE INDEX idx_notification_analytics_sent_at ON iosapp.notification_analytics(sent_at);
CREATE INDEX idx_notification_analytics_type ON iosapp.notification_analytics(notification_type);

-- STEP 9: Create materialized views for analytics with proper relationships
-- =========================================================================

CREATE MATERIALIZED VIEW iosapp.daily_user_stats AS
SELECT 
    DATE(us.session_start) as date,
    COUNT(DISTINCT us.user_id) as active_users,
    COUNT(us.id) as total_sessions,
    AVG(us.duration_seconds) as avg_session_duration,
    SUM(us.jobs_viewed_count) as total_jobs_viewed,
    SUM(us.jobs_saved_count) as total_jobs_saved,
    SUM(us.searches_performed) as total_searches,
    -- New metrics with proper relationships
    COUNT(DISTINCT sa.id) as actual_searches_performed,
    COUNT(DISTINCT je.id) as job_engagements_created,
    COUNT(DISTINCT ua.id) as total_user_actions
FROM iosapp.user_sessions us
LEFT JOIN iosapp.search_analytics sa ON us.id = sa.session_id
LEFT JOIN iosapp.job_engagement je ON us.id = je.session_id
LEFT JOIN iosapp.user_actions ua ON us.id = ua.session_id
WHERE us.session_start >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(us.session_start)
ORDER BY date DESC;

CREATE MATERIALIZED VIEW iosapp.user_engagement_summary AS
SELECT 
    u.id as user_id,
    u.email,
    u.created_at as user_since,
    COUNT(DISTINCT us.id) as total_sessions,
    SUM(us.duration_seconds) as total_time_spent,
    COUNT(DISTINCT je.job_id) as unique_jobs_viewed,
    COUNT(sj.id) as total_jobs_saved,
    COUNT(DISTINCT sa.id) as total_searches,
    AVG(je.engagement_score) as avg_engagement_score,
    MAX(us.session_start) as last_active,
    -- New metrics with proper relationships
    COUNT(DISTINCT na.id) as total_notifications_received,
    COUNT(DISTINCT CASE WHEN na.opened_at IS NOT NULL THEN na.id END) as notifications_opened,
    COUNT(DISTINCT sa.session_id) as sessions_with_searches,
    COUNT(DISTINCT je.session_id) as sessions_with_job_engagement,
    COUNT(DISTINCT ua.id) as total_user_actions
FROM iosapp.users u
LEFT JOIN iosapp.user_sessions us ON u.id = us.user_id
LEFT JOIN iosapp.job_engagement je ON u.id = je.user_id
LEFT JOIN iosapp.saved_jobs sj ON u.id = sj.user_id
LEFT JOIN iosapp.search_analytics sa ON u.id = sa.user_id
LEFT JOIN iosapp.notification_analytics na ON u.id = na.user_id
LEFT JOIN iosapp.user_actions ua ON u.id = ua.user_id
GROUP BY u.id, u.email, u.created_at;

-- Create comprehensive session analytics view
CREATE MATERIALIZED VIEW iosapp.session_analytics_comprehensive AS
SELECT 
    us.id as session_id,
    us.user_id,
    us.session_start,
    us.session_end,
    us.duration_seconds,
    us.actions_count,
    us.jobs_viewed_count,
    us.jobs_saved_count,
    us.searches_performed,
    
    -- Related search analytics (properly linked via session_id)
    COUNT(DISTINCT sa.id) as actual_searches_in_session,
    AVG(sa.results_count) as avg_search_results,
    AVG(sa.clicked_results) as avg_search_clicks,
    
    -- Related job engagement (properly linked via session_id)
    COUNT(DISTINCT je.id) as job_engagements_in_session,
    AVG(je.total_view_time) as avg_job_view_time,
    AVG(je.engagement_score) as avg_engagement_score,
    
    -- Related notifications (through job engagement)
    COUNT(DISTINCT na.id) as notifications_leading_to_session,
    
    -- User actions breakdown (properly linked via session_id)
    COUNT(DISTINCT ua.id) as total_actions_recorded,
    COUNT(DISTINCT CASE WHEN ua.action_type = 'search' THEN ua.id END) as search_actions,
    COUNT(DISTINCT CASE WHEN ua.action_type = 'view_job' THEN ua.id END) as job_view_actions,
    COUNT(DISTINCT CASE WHEN ua.action_type = 'save_job' THEN ua.id END) as job_save_actions

FROM iosapp.user_sessions us
LEFT JOIN iosapp.search_analytics sa ON us.id = sa.session_id
LEFT JOIN iosapp.job_engagement je ON us.id = je.session_id
LEFT JOIN iosapp.user_actions ua ON us.id = ua.session_id
LEFT JOIN iosapp.notification_analytics na ON je.id = na.job_engagement_id
WHERE us.session_start >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY us.id, us.user_id, us.session_start, us.session_end, us.duration_seconds, 
         us.actions_count, us.jobs_viewed_count, us.jobs_saved_count, us.searches_performed;

-- Create indexes on materialized views
CREATE INDEX idx_daily_user_stats_date ON iosapp.daily_user_stats(date);
CREATE INDEX idx_user_engagement_summary_user_id ON iosapp.user_engagement_summary(user_id);
CREATE INDEX idx_user_engagement_summary_last_active ON iosapp.user_engagement_summary(last_active);
CREATE INDEX idx_session_analytics_comprehensive_session_id ON iosapp.session_analytics_comprehensive(session_id);
CREATE INDEX idx_session_analytics_comprehensive_user_id ON iosapp.session_analytics_comprehensive(user_id);
CREATE INDEX idx_session_analytics_comprehensive_session_start ON iosapp.session_analytics_comprehensive(session_start);

-- STEP 10: Create update triggers for timestamps
-- ==============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER update_user_sessions_updated_at 
    BEFORE UPDATE ON iosapp.user_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_engagement_updated_at 
    BEFORE UPDATE ON iosapp.job_engagement 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Summary: Analytics schema recreated with proper RDBMS relationships
-- ===================================================================
-- 
-- Tables created with full foreign key relationships:
-- 1. user_sessions (foundation table)
-- 2. search_analytics (linked to sessions)
-- 3. user_actions (linked to sessions, jobs, searches)
-- 4. job_engagement (linked to sessions, jobs) 
-- 5. user_preferences_history (linked to users)
-- 6. notification_analytics (linked to users, devices, jobs, job_engagement)
-- 
-- Total foreign key relationships: 15+
-- All tables are now properly connected following RDBMS principles
-- Comprehensive materialized views enable advanced analytics with proper JOINs