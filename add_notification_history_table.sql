-- Add job notification history table for duplicate prevention
-- This table tracks which users have been notified about specific jobs

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
    
    -- Unique constraint to prevent duplicate notifications for same job
    CONSTRAINT uq_user_job_notification UNIQUE (user_id, job_unique_key)
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_notification_history_user_id ON iosapp.job_notification_history(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_job_key ON iosapp.job_notification_history(job_unique_key);
CREATE INDEX IF NOT EXISTS idx_notification_history_sent_at ON iosapp.job_notification_history(notification_sent_at);
CREATE INDEX IF NOT EXISTS idx_notification_history_job_id ON iosapp.job_notification_history(job_id);

-- Add comment
COMMENT ON TABLE iosapp.job_notification_history IS 'Tracks which users have been notified about specific jobs to prevent duplicates';
COMMENT ON COLUMN iosapp.job_notification_history.job_unique_key IS 'MD5 hash of normalized company + title for duplicate detection';
COMMENT ON COLUMN iosapp.job_notification_history.matched_keywords IS 'JSON array of keywords that matched for this notification';

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON iosapp.job_notification_history TO your_app_user;