-- Migration to add soft delete functionality to job_notification_history table
-- This allows users to delete notifications in the iOS app while preserving unique keys

BEGIN;

-- Add new columns to job_notification_history table for soft delete functionality
ALTER TABLE iosapp.job_notification_history 
ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

-- Create index for faster queries on deleted notifications
CREATE INDEX IF NOT EXISTS idx_job_notification_history_is_deleted 
ON iosapp.job_notification_history(is_deleted);

-- Create index for faster queries on read notifications
CREATE INDEX IF NOT EXISTS idx_job_notification_history_is_read 
ON iosapp.job_notification_history(is_read);

-- Create composite index for user notifications that are not deleted
CREATE INDEX IF NOT EXISTS idx_job_notification_history_user_not_deleted 
ON iosapp.job_notification_history(user_id, is_deleted) 
WHERE is_deleted = FALSE;

-- Update any existing records to have is_read = FALSE and is_deleted = FALSE
UPDATE iosapp.job_notification_history 
SET is_read = FALSE, is_deleted = FALSE 
WHERE is_read IS NULL OR is_deleted IS NULL;

-- Make the new columns NOT NULL now that they have default values
ALTER TABLE iosapp.job_notification_history 
ALTER COLUMN is_read SET NOT NULL,
ALTER COLUMN is_deleted SET NOT NULL;

COMMIT;

-- Verify the changes
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_schema = 'iosapp' 
AND table_name = 'job_notification_history'
AND column_name IN ('is_read', 'is_deleted', 'deleted_at');