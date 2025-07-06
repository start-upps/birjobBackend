-- ALTER commands to properly connect notification tables with foreign key relationships
-- Run these after creating the initial notification tables

-- =====================================================
-- 1. ADD MISSING FOREIGN KEY CONSTRAINTS
-- =====================================================

-- Ensure job_notification_history has proper unique constraint
ALTER TABLE iosapp.job_notification_history 
ADD CONSTRAINT uq_user_job_notification UNIQUE (user_id, job_unique_key);

-- =====================================================
-- 2. ADD CROSS-REFERENCES BETWEEN NOTIFICATION TABLES
-- =====================================================

-- Add reference from push_notifications to job_notification_history
-- (This allows tracking which push notification was sent for which job match)
ALTER TABLE iosapp.push_notifications 
ADD COLUMN job_notification_id UUID;

ALTER TABLE iosapp.push_notifications 
ADD CONSTRAINT fk_push_notifications_job_notification
FOREIGN KEY (job_notification_id) REFERENCES iosapp.job_notification_history(id) ON DELETE SET NULL;

-- Add reference from notification_delivery_log to job_notification_history
ALTER TABLE iosapp.notification_delivery_log 
ADD COLUMN job_notification_id UUID;

ALTER TABLE iosapp.notification_delivery_log 
ADD CONSTRAINT fk_delivery_log_job_notification
FOREIGN KEY (job_notification_id) REFERENCES iosapp.job_notification_history(id) ON DELETE SET NULL;

-- =====================================================
-- 3. CREATE NOTIFICATION_STATS TABLE (instead of view)
-- =====================================================

-- Create actual table for notification statistics with relationships
CREATE TABLE iosapp.notification_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date_period DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL CHECK (period_type IN ('daily', 'weekly', 'monthly')),
    
    -- Statistics
    total_notifications INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    unique_jobs INTEGER DEFAULT 0,
    avg_keywords_matched DECIMAL(5,2) DEFAULT 0,
    
    -- Breakdown by notification type
    job_match_notifications INTEGER DEFAULT 0,
    daily_digest_notifications INTEGER DEFAULT 0,
    system_notifications INTEGER DEFAULT 0,
    
    -- Success rates
    successful_deliveries INTEGER DEFAULT 0,
    failed_deliveries INTEGER DEFAULT 0,
    delivery_success_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint
    UNIQUE(date_period, period_type)
);

-- =====================================================
-- 4. CREATE USER_NOTIFICATION_SUMMARY TABLE (instead of view)
-- =====================================================

-- Create actual table for user notification summary with relationships
CREATE TABLE iosapp.user_notification_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES iosapp.users(id) ON DELETE CASCADE,
    device_id UUID NOT NULL REFERENCES iosapp.device_tokens(id) ON DELETE CASCADE,
    
    -- User info (denormalized for performance)
    email VARCHAR(255),
    device_token VARCHAR(500),
    
    -- Notification preferences
    job_matches_enabled BOOLEAN DEFAULT TRUE,
    daily_digest_enabled BOOLEAN DEFAULT TRUE,
    keywords JSONB DEFAULT '[]'::jsonb,
    
    -- Statistics
    total_notifications_received INTEGER DEFAULT 0,
    total_notifications_sent INTEGER DEFAULT 0,
    total_notifications_failed INTEGER DEFAULT 0,
    unique_jobs_notified INTEGER DEFAULT 0,
    
    -- Timestamps
    first_notification_at TIMESTAMP WITH TIME ZONE,
    last_notification_at TIMESTAMP WITH TIME ZONE,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Performance metrics
    avg_response_time_ms INTEGER DEFAULT 0,
    delivery_success_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Ensure one summary per user-device combination
    UNIQUE(user_id, device_id)
);

-- =====================================================
-- 5. ADD INDEXES FOR NEW RELATIONSHIPS
-- =====================================================

-- Indexes for new foreign key columns
CREATE INDEX IF NOT EXISTS idx_push_notifications_job_notification_id 
ON iosapp.push_notifications(job_notification_id);

CREATE INDEX IF NOT EXISTS idx_delivery_log_job_notification_id 
ON iosapp.notification_delivery_log(job_notification_id);

-- Indexes for stats table
CREATE INDEX IF NOT EXISTS idx_notification_stats_date_period 
ON iosapp.notification_stats(date_period);

CREATE INDEX IF NOT EXISTS idx_notification_stats_period_type 
ON iosapp.notification_stats(period_type);

-- Indexes for summary table
CREATE INDEX IF NOT EXISTS idx_user_notification_summary_user_id 
ON iosapp.user_notification_summary(user_id);

CREATE INDEX IF NOT EXISTS idx_user_notification_summary_device_id 
ON iosapp.user_notification_summary(device_id);

CREATE INDEX IF NOT EXISTS idx_user_notification_summary_last_notification 
ON iosapp.user_notification_summary(last_notification_at);

-- =====================================================
-- 6. CREATE TRIGGER FUNCTIONS FOR AUTO-UPDATING STATS
-- =====================================================

-- Function to update user notification summary
CREATE OR REPLACE FUNCTION update_user_notification_summary()
RETURNS TRIGGER AS $$
BEGIN
    -- Update or insert user notification summary
    INSERT INTO iosapp.user_notification_summary (
        user_id, device_id, email, device_token, 
        total_notifications_received, unique_jobs_notified,
        first_notification_at, last_notification_at, last_updated_at
    )
    SELECT 
        NEW.user_id,
        dt.id as device_id,
        u.email,
        dt.device_token,
        1,
        1,
        NEW.notification_sent_at,
        NEW.notification_sent_at,
        NOW()
    FROM iosapp.users u
    JOIN iosapp.device_tokens dt ON u.id = dt.user_id
    WHERE u.id = NEW.user_id AND dt.is_active = true
    LIMIT 1
    ON CONFLICT (user_id, device_id) DO UPDATE SET
        total_notifications_received = user_notification_summary.total_notifications_received + 1,
        unique_jobs_notified = (
            SELECT COUNT(DISTINCT job_id) 
            FROM iosapp.job_notification_history 
            WHERE user_id = NEW.user_id
        ),
        last_notification_at = NEW.notification_sent_at,
        last_updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update notification stats
CREATE OR REPLACE FUNCTION update_notification_stats()
RETURNS TRIGGER AS $$
DECLARE
    stats_date DATE;
BEGIN
    stats_date := DATE(NEW.notification_sent_at);
    
    -- Update daily stats
    INSERT INTO iosapp.notification_stats (
        date_period, period_type, total_notifications, unique_users, unique_jobs
    )
    VALUES (
        stats_date,
        'daily',
        1,
        1,
        1
    )
    ON CONFLICT (date_period, period_type) DO UPDATE SET
        total_notifications = notification_stats.total_notifications + 1,
        unique_users = (
            SELECT COUNT(DISTINCT user_id) 
            FROM iosapp.job_notification_history 
            WHERE DATE(notification_sent_at) = stats_date
        ),
        unique_jobs = (
            SELECT COUNT(DISTINCT job_id) 
            FROM iosapp.job_notification_history 
            WHERE DATE(notification_sent_at) = stats_date
        ),
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 7. CREATE TRIGGERS FOR AUTO-UPDATING
-- =====================================================

-- Trigger to update user summary when notification is sent
CREATE TRIGGER trigger_update_user_notification_summary
    AFTER INSERT ON iosapp.job_notification_history
    FOR EACH ROW
    EXECUTE FUNCTION update_user_notification_summary();

-- Trigger to update notification stats when notification is sent
CREATE TRIGGER trigger_update_notification_stats
    AFTER INSERT ON iosapp.job_notification_history
    FOR EACH ROW
    EXECUTE FUNCTION update_notification_stats();

-- =====================================================
-- 8. ADD RELATIONSHIP TO EXISTING SCRAPER JOBS TABLE
-- =====================================================

-- Add optional reference to actual job in scraper database
-- (This creates a soft relationship since scraper.jobs_jobpost data gets truncated)
ALTER TABLE iosapp.job_notification_history 
ADD COLUMN source_job_reference JSONB;

-- Add comment explaining the relationship
COMMENT ON COLUMN iosapp.job_notification_history.source_job_reference IS 
'Cached copy of job data from scraper.jobs_jobpost since original data gets truncated hourly';

-- =====================================================
-- 9. CREATE CLEANUP PROCEDURES
-- =====================================================

-- Function to cleanup old notification data
CREATE OR REPLACE FUNCTION cleanup_old_notifications(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete old notification history
    DELETE FROM iosapp.job_notification_history 
    WHERE notification_sent_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Delete old delivery logs
    DELETE FROM iosapp.notification_delivery_log 
    WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    -- Delete old push notification records
    DELETE FROM iosapp.push_notifications 
    WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 10. POPULATE INITIAL DATA
-- =====================================================

-- Populate user notification summaries for existing users
INSERT INTO iosapp.user_notification_summary (
    user_id, device_id, email, device_token, job_matches_enabled, keywords
)
SELECT DISTINCT 
    u.id as user_id,
    dt.id as device_id,
    u.email,
    dt.device_token,
    COALESCE(u.notifications_enabled, true) as job_matches_enabled,
    COALESCE(u.keywords, '[]'::jsonb) as keywords
FROM iosapp.users u
JOIN iosapp.device_tokens dt ON u.id = dt.user_id
WHERE dt.is_active = true
ON CONFLICT (user_id, device_id) DO UPDATE SET
    email = EXCLUDED.email,
    device_token = EXCLUDED.device_token,
    job_matches_enabled = EXCLUDED.job_matches_enabled,
    keywords = EXCLUDED.keywords,
    last_updated_at = NOW();

-- Initialize current day stats
INSERT INTO iosapp.notification_stats (date_period, period_type)
VALUES (CURRENT_DATE, 'daily')
ON CONFLICT (date_period, period_type) DO NOTHING;

-- =====================================================
-- 11. CREATE USEFUL QUERY FUNCTIONS
-- =====================================================

-- Function to get notification analytics for a date range
CREATE OR REPLACE FUNCTION get_notification_analytics(
    start_date DATE DEFAULT CURRENT_DATE - INTERVAL '7 days',
    end_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    date_period DATE,
    total_notifications INTEGER,
    unique_users INTEGER,
    unique_jobs INTEGER,
    delivery_rate DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ns.date_period,
        ns.total_notifications,
        ns.unique_users,
        ns.unique_jobs,
        CASE 
            WHEN ns.total_notifications > 0 
            THEN ROUND((ns.successful_deliveries::DECIMAL / ns.total_notifications) * 100, 2)
            ELSE 0 
        END as delivery_rate
    FROM iosapp.notification_stats ns
    WHERE ns.date_period BETWEEN start_date AND end_date
        AND ns.period_type = 'daily'
    ORDER BY ns.date_period DESC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Check all foreign key relationships
/*
SELECT 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_schema = 'iosapp' 
    AND tc.table_name LIKE '%notification%'
ORDER BY tc.table_name, kcu.column_name;
*/

-- Check table relationships
/*
SELECT 
    schemaname, 
    tablename, 
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'iosapp' 
    AND tablename LIKE '%notification%'
ORDER BY tablename, indexname;
*/