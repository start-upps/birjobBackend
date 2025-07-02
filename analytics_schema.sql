-- Enhanced Analytics Schema with Proper RDBMS Relationships
-- This extends the existing schema with comprehensive analytics tables

-- Create user_sessions table for tracking app usage
CREATE TABLE IF NOT EXISTS iosapp.user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                           -- FOREIGN KEY to users.id
    device_id VARCHAR(255) NOT NULL,                 -- For cross-reference
    session_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,                        -- Calculated duration
    app_version VARCHAR(20),                         -- App version during session
    os_version VARCHAR(20),                          -- OS version during session
    actions_count INTEGER DEFAULT 0,                 -- Number of actions in session
    jobs_viewed_count INTEGER DEFAULT 0,             -- Jobs viewed in session
    jobs_saved_count INTEGER DEFAULT 0,              -- Jobs saved in session
    searches_performed INTEGER DEFAULT 0,            -- Searches performed in session
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_user_sessions_user FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
    
    -- Check Constraints
    CONSTRAINT session_duration_positive CHECK (duration_seconds >= 0),
    CONSTRAINT session_end_after_start CHECK (session_end >= session_start OR session_end IS NULL),
    CONSTRAINT actions_count_positive CHECK (actions_count >= 0)
);

-- Create user_actions table for detailed action tracking
CREATE TABLE IF NOT EXISTS iosapp.user_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                           -- FOREIGN KEY to users.id
    session_id UUID,                                  -- FOREIGN KEY to user_sessions.id
    action_type VARCHAR(50) NOT NULL,                 -- Type of action (view_job, save_job, search, etc.)
    action_details JSONB DEFAULT '{}'::jsonb,        -- Additional action data
    job_id INTEGER,                                   -- Job ID if action relates to job
    search_query VARCHAR(500),                        -- Search query if action is search
    page_url VARCHAR(500),                           -- Page/screen where action occurred
    duration_seconds INTEGER DEFAULT 0,              -- Time spent on action
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_user_actions_user FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_actions_session FOREIGN KEY (session_id) REFERENCES iosapp.user_sessions(id) ON DELETE SET NULL,
    
    -- Check Constraints
    CONSTRAINT action_duration_positive CHECK (duration_seconds >= 0),
    CONSTRAINT action_type_not_empty CHECK (length(action_type) > 0)
);

-- Create search_analytics table for search behavior analysis
CREATE TABLE IF NOT EXISTS iosapp.search_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                           -- FOREIGN KEY to users.id
    search_query VARCHAR(500) NOT NULL,              -- The search query
    normalized_query VARCHAR(500),                   -- Cleaned/normalized version
    results_count INTEGER DEFAULT 0,                 -- Number of results returned
    clicked_results INTEGER DEFAULT 0,               -- Number of results clicked
    time_to_first_click INTEGER,                     -- Milliseconds to first click
    total_session_time INTEGER DEFAULT 0,            -- Total time spent on results
    filters_applied JSONB DEFAULT '{}'::jsonb,       -- Filters used (location, salary, etc.)
    result_job_ids JSONB DEFAULT '[]'::jsonb,        -- Array of job IDs in results
    clicked_job_ids JSONB DEFAULT '[]'::jsonb,       -- Array of clicked job IDs
    search_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_search_analytics_user FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
    
    -- Check Constraints
    CONSTRAINT results_count_positive CHECK (results_count >= 0),
    CONSTRAINT clicked_results_reasonable CHECK (clicked_results <= results_count),
    CONSTRAINT search_query_not_empty CHECK (length(search_query) > 0)
);

-- Create job_engagement table for detailed job interaction tracking
CREATE TABLE IF NOT EXISTS iosapp.job_engagement (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                           -- FOREIGN KEY to users.id
    job_id INTEGER NOT NULL,                         -- The job being engaged with
    job_title VARCHAR(500),                          -- Cached job title
    job_company VARCHAR(255),                        -- Cached job company
    job_source VARCHAR(100),                         -- Cached job source
    job_location VARCHAR(255),                       -- Cached job location
    
    -- Engagement metrics
    total_view_time INTEGER DEFAULT 0,               -- Total time spent viewing (seconds)
    view_count INTEGER DEFAULT 0,                    -- Number of times viewed
    first_viewed_at TIMESTAMP WITH TIME ZONE,        -- First time user viewed this job
    last_viewed_at TIMESTAMP WITH TIME ZONE,         -- Most recent view
    
    -- User actions on this job
    is_saved BOOLEAN DEFAULT FALSE,                  -- Whether job is currently saved
    saved_at TIMESTAMP WITH TIME ZONE,               -- When job was saved
    unsaved_at TIMESTAMP WITH TIME ZONE,             -- When job was unsaved (if applicable)
    
    -- Application tracking
    applied BOOLEAN DEFAULT FALSE,                   -- Whether user applied
    applied_at TIMESTAMP WITH TIME ZONE,             -- When application was submitted
    application_source VARCHAR(100),                 -- How they applied (app, external, etc.)
    
    -- Engagement scoring
    engagement_score INTEGER DEFAULT 0,              -- Calculated engagement score (0-100)
    last_calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_job_engagement_user FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
    
    -- Unique Constraints
    CONSTRAINT unique_user_job_engagement UNIQUE(user_id, job_id),
    
    -- Check Constraints
    CONSTRAINT view_time_positive CHECK (total_view_time >= 0),
    CONSTRAINT view_count_positive CHECK (view_count >= 0),
    CONSTRAINT engagement_score_range CHECK (engagement_score >= 0 AND engagement_score <= 100),
    CONSTRAINT last_viewed_after_first CHECK (last_viewed_at >= first_viewed_at OR last_viewed_at IS NULL)
);

-- Create user_preferences_history table for tracking preference changes
CREATE TABLE IF NOT EXISTS iosapp.user_preferences_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                           -- FOREIGN KEY to users.id
    change_type VARCHAR(50) NOT NULL,                -- Type of change (keywords_updated, sources_updated, etc.)
    old_value JSONB,                                 -- Previous value
    new_value JSONB,                                 -- New value
    change_reason VARCHAR(100),                      -- Reason for change (user_action, recommendation, etc.)
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_user_preferences_history_user FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
    
    -- Check Constraints
    CONSTRAINT change_type_not_empty CHECK (length(change_type) > 0)
);

-- Create notification_analytics table for push notification tracking
CREATE TABLE IF NOT EXISTS iosapp.notification_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                           -- FOREIGN KEY to users.id
    device_token_id UUID,                            -- FOREIGN KEY to device_tokens.id
    notification_type VARCHAR(50) NOT NULL,          -- Type of notification (job_match, reminder, etc.)
    notification_title VARCHAR(200),                 -- Notification title
    notification_body TEXT,                          -- Notification body
    job_id INTEGER,                                   -- Related job ID (if applicable)
    
    -- Delivery tracking
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP WITH TIME ZONE,           -- When notification was delivered
    opened_at TIMESTAMP WITH TIME ZONE,              -- When user opened notification
    clicked_at TIMESTAMP WITH TIME ZONE,             -- When user clicked notification
    
    -- Status tracking
    delivery_status VARCHAR(20) DEFAULT 'sent',      -- sent, delivered, failed
    error_message TEXT,                              -- Error details if failed
    
    -- Engagement tracking
    led_to_app_open BOOLEAN DEFAULT FALSE,           -- Whether notification led to app open
    led_to_job_view BOOLEAN DEFAULT FALSE,           -- Whether led to viewing the job
    led_to_job_save BOOLEAN DEFAULT FALSE,           -- Whether led to saving the job
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_notification_analytics_user FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
    CONSTRAINT fk_notification_analytics_device FOREIGN KEY (device_token_id) REFERENCES iosapp.device_tokens(id) ON DELETE SET NULL,
    
    -- Check Constraints
    CONSTRAINT notification_type_not_empty CHECK (length(notification_type) > 0),
    CONSTRAINT delivery_status_valid CHECK (delivery_status IN ('sent', 'delivered', 'failed', 'pending'))
);

-- Create indexes for analytics performance
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON iosapp.user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_start_time ON iosapp.user_sessions(session_start);
CREATE INDEX IF NOT EXISTS idx_user_sessions_device_id ON iosapp.user_sessions(device_id);

CREATE INDEX IF NOT EXISTS idx_user_actions_user_id ON iosapp.user_actions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_actions_session_id ON iosapp.user_actions(session_id);
CREATE INDEX IF NOT EXISTS idx_user_actions_type ON iosapp.user_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_user_actions_timestamp ON iosapp.user_actions(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_actions_job_id ON iosapp.user_actions(job_id) WHERE job_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_search_analytics_user_id ON iosapp.search_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_search_analytics_query ON iosapp.search_analytics(search_query);
CREATE INDEX IF NOT EXISTS idx_search_analytics_timestamp ON iosapp.search_analytics(search_timestamp);

CREATE INDEX IF NOT EXISTS idx_job_engagement_user_id ON iosapp.job_engagement(user_id);
CREATE INDEX IF NOT EXISTS idx_job_engagement_job_id ON iosapp.job_engagement(job_id);
CREATE INDEX IF NOT EXISTS idx_job_engagement_last_viewed ON iosapp.job_engagement(last_viewed_at);
CREATE INDEX IF NOT EXISTS idx_job_engagement_engagement_score ON iosapp.job_engagement(engagement_score);

CREATE INDEX IF NOT EXISTS idx_user_preferences_history_user_id ON iosapp.user_preferences_history(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_history_changed_at ON iosapp.user_preferences_history(changed_at);
CREATE INDEX IF NOT EXISTS idx_user_preferences_history_change_type ON iosapp.user_preferences_history(change_type);

CREATE INDEX IF NOT EXISTS idx_notification_analytics_user_id ON iosapp.notification_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_analytics_device_token_id ON iosapp.notification_analytics(device_token_id);
CREATE INDEX IF NOT EXISTS idx_notification_analytics_sent_at ON iosapp.notification_analytics(sent_at);
CREATE INDEX IF NOT EXISTS idx_notification_analytics_type ON iosapp.notification_analytics(notification_type);
CREATE INDEX IF NOT EXISTS idx_notification_analytics_job_id ON iosapp.notification_analytics(job_id) WHERE job_id IS NOT NULL;

-- Create update triggers for timestamps
CREATE TRIGGER update_user_sessions_updated_at 
    BEFORE UPDATE ON iosapp.user_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_engagement_updated_at 
    BEFORE UPDATE ON iosapp.job_engagement 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create materialized views for common analytics queries
CREATE MATERIALIZED VIEW IF NOT EXISTS iosapp.daily_user_stats AS
SELECT 
    DATE(us.session_start) as date,
    COUNT(DISTINCT us.user_id) as active_users,
    COUNT(us.id) as total_sessions,
    AVG(us.duration_seconds) as avg_session_duration,
    SUM(us.jobs_viewed_count) as total_jobs_viewed,
    SUM(us.jobs_saved_count) as total_jobs_saved,
    SUM(us.searches_performed) as total_searches
FROM iosapp.user_sessions us
WHERE us.session_start >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(us.session_start)
ORDER BY date DESC;

CREATE MATERIALIZED VIEW IF NOT EXISTS iosapp.user_engagement_summary AS
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
    MAX(us.session_start) as last_active
FROM iosapp.users u
LEFT JOIN iosapp.user_sessions us ON u.id = us.user_id
LEFT JOIN iosapp.job_engagement je ON u.id = je.user_id
LEFT JOIN iosapp.saved_jobs sj ON u.id = sj.user_id
LEFT JOIN iosapp.search_analytics sa ON u.id = sa.user_id
GROUP BY u.id, u.email, u.created_at;

-- Create indexes on materialized views
CREATE INDEX IF NOT EXISTS idx_daily_user_stats_date ON iosapp.daily_user_stats(date);
CREATE INDEX IF NOT EXISTS idx_user_engagement_summary_user_id ON iosapp.user_engagement_summary(user_id);
CREATE INDEX IF NOT EXISTS idx_user_engagement_summary_last_active ON iosapp.user_engagement_summary(last_active);

-- Summary of analytics tables created:
-- 1. user_sessions - App usage sessions with duration and activity metrics
-- 2. user_actions - Detailed action tracking within sessions
-- 3. search_analytics - Search behavior and effectiveness analysis
-- 4. job_engagement - Comprehensive job interaction tracking
-- 5. user_preferences_history - Track changes to user preferences
-- 6. notification_analytics - Push notification delivery and engagement
-- 7. daily_user_stats (materialized view) - Daily aggregated statistics
-- 8. user_engagement_summary (materialized view) - Per-user engagement summary

-- Total: 6 analytics tables + 2 materialized views with proper RDBMS relationships