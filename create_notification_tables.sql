-- Complete notification system database migration
-- Creates all required tables with proper RDBMS relationships

-- =====================================================
-- 1. JOB NOTIFICATION HISTORY TABLE
-- =====================================================
-- Tracks which users have been notified about specific jobs to prevent duplicates
CREATE TABLE IF NOT EXISTS iosapp.job_notification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES iosapp.users(id) ON DELETE CASCADE,
    job_unique_key VARCHAR(255) NOT NULL,  -- MD5 hash of company + title
    job_id INTEGER NOT NULL,
    job_title VARCHAR(500) NOT NULL,
    job_company VARCHAR(255) NOT NULL,
    job_source VARCHAR(100),
    matched_keywords JSONB DEFAULT '[]'::jsonb,
    notification_sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicate notifications for same job
    CONSTRAINT uq_user_job_notification UNIQUE (user_id, job_unique_key)
);

-- =====================================================
-- 2. PUSH NOTIFICATIONS TABLE  
-- =====================================================
-- Tracks all push notifications sent via APNs
CREATE TABLE IF NOT EXISTS iosapp.push_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES iosapp.device_tokens(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES iosapp.users(id) ON DELETE CASCADE,
    match_id UUID REFERENCES iosapp.job_notification_history(id) ON DELETE SET NULL,
    notification_type VARCHAR(50) NOT NULL CHECK (notification_type IN ('job_match', 'daily_digest', 'system')),
    payload JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'cancelled')),
    apns_response JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 3. NOTIFICATION SETTINGS TABLE
-- =====================================================
-- Extended user notification preferences
CREATE TABLE IF NOT EXISTS iosapp.notification_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES iosapp.users(id) ON DELETE CASCADE,
    device_id UUID NOT NULL REFERENCES iosapp.device_tokens(id) ON DELETE CASCADE,
    
    -- Notification preferences
    job_matches_enabled BOOLEAN DEFAULT TRUE,
    daily_digest_enabled BOOLEAN DEFAULT TRUE,
    system_notifications_enabled BOOLEAN DEFAULT TRUE,
    
    -- Timing preferences
    quiet_hours_start INTEGER DEFAULT 22 CHECK (quiet_hours_start >= 0 AND quiet_hours_start <= 23),
    quiet_hours_end INTEGER DEFAULT 8 CHECK (quiet_hours_end >= 0 AND quiet_hours_end <= 23),
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Frequency limits
    max_notifications_per_hour INTEGER DEFAULT 5,
    max_notifications_per_day INTEGER DEFAULT 20,
    
    -- Keywords (denormalized for performance)
    keywords JSONB DEFAULT '[]'::jsonb,
    keyword_match_mode VARCHAR(20) DEFAULT 'any' CHECK (keyword_match_mode IN ('any', 'all')),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one settings record per user-device combination
    CONSTRAINT uq_user_device_settings UNIQUE (user_id, device_id)
);

-- =====================================================
-- 4. NOTIFICATION DELIVERY LOG
-- =====================================================
-- Detailed log of notification delivery attempts and results
CREATE TABLE IF NOT EXISTS iosapp.notification_delivery_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID NOT NULL REFERENCES iosapp.push_notifications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES iosapp.users(id) ON DELETE CASCADE,
    device_id UUID NOT NULL REFERENCES iosapp.device_tokens(id) ON DELETE CASCADE,
    
    -- Delivery details
    attempt_number INTEGER NOT NULL DEFAULT 1,
    delivery_status VARCHAR(20) NOT NULL CHECK (delivery_status IN ('success', 'failed', 'throttled', 'quiet_hours', 'device_inactive')),
    error_message TEXT,
    apns_message_id VARCHAR(255),
    apns_timestamp TIMESTAMP WITH TIME ZONE,
    
    -- Performance metrics
    processing_time_ms INTEGER,
    queue_time_ms INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- job_notification_history indexes
CREATE INDEX IF NOT EXISTS idx_notification_history_user_id ON iosapp.job_notification_history(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_job_key ON iosapp.job_notification_history(job_unique_key);
CREATE INDEX IF NOT EXISTS idx_notification_history_sent_at ON iosapp.job_notification_history(notification_sent_at);
CREATE INDEX IF NOT EXISTS idx_notification_history_job_id ON iosapp.job_notification_history(job_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_keywords ON iosapp.job_notification_history USING GIN (matched_keywords);

-- push_notifications indexes
CREATE INDEX IF NOT EXISTS idx_push_notifications_device_id ON iosapp.push_notifications(device_id);
CREATE INDEX IF NOT EXISTS idx_push_notifications_user_id ON iosapp.push_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_push_notifications_match_id ON iosapp.push_notifications(match_id);
CREATE INDEX IF NOT EXISTS idx_push_notifications_type ON iosapp.push_notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_push_notifications_status ON iosapp.push_notifications(status);
CREATE INDEX IF NOT EXISTS idx_push_notifications_created_at ON iosapp.push_notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_push_notifications_sent_at ON iosapp.push_notifications(sent_at);

-- notification_settings indexes
CREATE INDEX IF NOT EXISTS idx_notification_settings_user_id ON iosapp.notification_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_settings_device_id ON iosapp.notification_settings(device_id);
CREATE INDEX IF NOT EXISTS idx_notification_settings_keywords ON iosapp.notification_settings USING GIN (keywords);

-- notification_delivery_log indexes
CREATE INDEX IF NOT EXISTS idx_delivery_log_notification_id ON iosapp.notification_delivery_log(notification_id);
CREATE INDEX IF NOT EXISTS idx_delivery_log_user_id ON iosapp.notification_delivery_log(user_id);
CREATE INDEX IF NOT EXISTS idx_delivery_log_device_id ON iosapp.notification_delivery_log(device_id);
CREATE INDEX IF NOT EXISTS idx_delivery_log_status ON iosapp.notification_delivery_log(delivery_status);
CREATE INDEX IF NOT EXISTS idx_delivery_log_created_at ON iosapp.notification_delivery_log(created_at);

-- =====================================================
-- TRIGGERS FOR UPDATED_AT TIMESTAMPS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at columns
CREATE TRIGGER update_job_notification_history_updated_at 
    BEFORE UPDATE ON iosapp.job_notification_history 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_push_notifications_updated_at 
    BEFORE UPDATE ON iosapp.push_notifications 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_settings_updated_at 
    BEFORE UPDATE ON iosapp.notification_settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE iosapp.job_notification_history IS 'Tracks which users have been notified about specific jobs to prevent duplicates';
COMMENT ON COLUMN iosapp.job_notification_history.job_unique_key IS 'MD5 hash of normalized company + title for duplicate detection';
COMMENT ON COLUMN iosapp.job_notification_history.matched_keywords IS 'JSON array of keywords that matched for this notification';

COMMENT ON TABLE iosapp.push_notifications IS 'Tracks all push notifications sent via APNs with delivery status';
COMMENT ON COLUMN iosapp.push_notifications.payload IS 'Full APNs payload sent to device';
COMMENT ON COLUMN iosapp.push_notifications.apns_response IS 'Response from APNs service';

COMMENT ON TABLE iosapp.notification_settings IS 'User-specific notification preferences and settings';
COMMENT ON COLUMN iosapp.notification_settings.keywords IS 'Denormalized keywords for fast matching queries';
COMMENT ON COLUMN iosapp.notification_settings.keyword_match_mode IS 'Whether to match ANY keyword or ALL keywords';

COMMENT ON TABLE iosapp.notification_delivery_log IS 'Detailed log of all notification delivery attempts for debugging and analytics';

-- =====================================================
-- INITIAL DATA MIGRATION
-- =====================================================

-- Migrate existing user keywords to notification_settings
INSERT INTO iosapp.notification_settings (user_id, device_id, keywords)
SELECT DISTINCT 
    u.id as user_id,
    dt.id as device_id,
    COALESCE(u.keywords, '[]'::jsonb) as keywords
FROM iosapp.users u
JOIN iosapp.device_tokens dt ON u.id = dt.user_id
WHERE dt.is_active = true
ON CONFLICT (user_id, device_id) DO UPDATE SET
    keywords = EXCLUDED.keywords,
    updated_at = NOW();

-- =====================================================
-- VIEWS FOR EASY QUERYING
-- =====================================================

-- View for notification statistics
CREATE OR REPLACE VIEW iosapp.v_notification_stats AS
SELECT 
    DATE_TRUNC('day', jnh.notification_sent_at) as notification_date,
    COUNT(*) as total_notifications,
    COUNT(DISTINCT jnh.user_id) as unique_users,
    COUNT(DISTINCT jnh.job_id) as unique_jobs,
    AVG(jsonb_array_length(jnh.matched_keywords)) as avg_keywords_matched
FROM iosapp.job_notification_history jnh
WHERE jnh.notification_sent_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', jnh.notification_sent_at)
ORDER BY notification_date DESC;

-- View for user notification summary
CREATE OR REPLACE VIEW iosapp.v_user_notification_summary AS
SELECT 
    u.id as user_id,
    u.email,
    dt.device_id,
    ns.job_matches_enabled,
    ns.keywords,
    COUNT(jnh.id) as total_notifications_received,
    MAX(jnh.notification_sent_at) as last_notification_at,
    COUNT(DISTINCT jnh.job_id) as unique_jobs_notified
FROM iosapp.users u
JOIN iosapp.device_tokens dt ON u.id = dt.user_id AND dt.is_active = true
LEFT JOIN iosapp.notification_settings ns ON u.id = ns.user_id AND dt.id = ns.device_id
LEFT JOIN iosapp.job_notification_history jnh ON u.id = jnh.user_id
GROUP BY u.id, u.email, dt.device_id, ns.job_matches_enabled, ns.keywords;

-- =====================================================
-- SAMPLE QUERIES FOR TESTING
-- =====================================================

-- Check table creation
-- SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'iosapp' AND tablename LIKE '%notification%';

-- Check foreign key relationships
-- SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name 
-- FROM information_schema.table_constraints AS tc 
-- JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
-- JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
-- WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'iosapp' AND tc.table_name LIKE '%notification%';

-- Check notification settings migration
-- SELECT COUNT(*) FROM iosapp.notification_settings;

-- =====================================================
-- PERMISSIONS (Uncomment and adjust as needed)
-- =====================================================

-- GRANT SELECT, INSERT, UPDATE, DELETE ON iosapp.job_notification_history TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON iosapp.push_notifications TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON iosapp.notification_settings TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON iosapp.notification_delivery_log TO your_app_user;
-- GRANT SELECT ON iosapp.v_notification_stats TO your_app_user;
-- GRANT SELECT ON iosapp.v_user_notification_summary TO your_app_user;