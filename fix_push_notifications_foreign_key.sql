-- Fix the foreign key constraint issue in push_notifications table
-- The error shows it's looking for match_id in job_notification_history table

-- First, let's see what columns exist in push_notifications
-- SELECT column_name, data_type, is_nullable FROM information_schema.columns 
-- WHERE table_name = 'push_notifications' AND table_schema = 'iosapp';

-- Check what foreign key constraints exist
-- SELECT tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
-- FROM information_schema.table_constraints AS tc 
-- JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
-- JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
-- WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = 'push_notifications';

-- Drop the problematic foreign key constraint
ALTER TABLE iosapp.push_notifications DROP CONSTRAINT IF EXISTS push_notifications_match_id_fkey;

-- Add the correct foreign key constraint to job_notification_history
ALTER TABLE iosapp.push_notifications 
ADD CONSTRAINT fk_push_notifications_job_notification_history
FOREIGN KEY (job_notification_id) REFERENCES iosapp.job_notification_history(id) ON DELETE SET NULL;

-- Update the column comment to clarify the relationship
COMMENT ON COLUMN iosapp.push_notifications.job_notification_id IS 'Foreign key to job_notification_history.id';