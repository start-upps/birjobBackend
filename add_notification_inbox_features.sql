-- Add notification inbox features to job_notification_history table
-- This adds read/unread functionality for notifications

-- Add is_read column for notification inbox
ALTER TABLE iosapp.job_notification_history 
ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT false;

-- Add updated_at column for tracking read status changes
ALTER TABLE iosapp.job_notification_history 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add index for better performance on inbox queries
CREATE INDEX IF NOT EXISTS idx_job_notification_history_user_id_sent_at 
ON iosapp.job_notification_history (user_id, notification_sent_at DESC);

CREATE INDEX IF NOT EXISTS idx_job_notification_history_is_read 
ON iosapp.job_notification_history (is_read);

CREATE INDEX IF NOT EXISTS idx_job_notification_history_keywords_time 
ON iosapp.job_notification_history (matched_keywords, notification_sent_at);

-- Add trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_notification_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_job_notification_history_updated_at ON iosapp.job_notification_history;
CREATE TRIGGER update_job_notification_history_updated_at
    BEFORE UPDATE ON iosapp.job_notification_history
    FOR EACH ROW
    EXECUTE FUNCTION update_notification_updated_at();

-- Update existing records to have proper timestamps
UPDATE iosapp.job_notification_history 
SET updated_at = notification_sent_at 
WHERE updated_at IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN iosapp.job_notification_history.is_read IS 'Whether the user has read this notification in the app';
COMMENT ON COLUMN iosapp.job_notification_history.updated_at IS 'Last time the notification record was updated (especially read status)';

-- Verification query to check the changes
-- SELECT column_name, data_type, is_nullable, column_default 
-- FROM information_schema.columns 
-- WHERE table_name = 'job_notification_history' 
-- AND table_schema = 'iosapp'
-- AND column_name IN ('is_read', 'updated_at');