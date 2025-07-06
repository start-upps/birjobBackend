-- SAFE DELETE all data from iosapp schema tables
-- This version includes safety checks and transaction handling
-- FOR DEVELOPMENT/TEST ENVIRONMENTS ONLY!

-- ========================================
-- SAFETY CHECKS - Uncomment and verify first
-- ========================================

-- 1. Verify you're in the correct database/environment
-- SELECT current_database(), current_user, inet_server_addr();

-- 2. Check current row counts before deletion
-- SELECT 'BEFORE DELETION - Row Counts:' as status;
-- SELECT 'users' as table_name, COUNT(*) as row_count FROM iosapp.users
-- UNION ALL
-- SELECT 'device_tokens', COUNT(*) FROM iosapp.device_tokens
-- UNION ALL
-- SELECT 'saved_jobs', COUNT(*) FROM iosapp.saved_jobs
-- UNION ALL
-- SELECT 'job_views', COUNT(*) FROM iosapp.job_views
-- UNION ALL
-- SELECT 'job_applications', COUNT(*) FROM iosapp.job_applications
-- UNION ALL
-- SELECT 'user_analytics', COUNT(*) FROM iosapp.user_analytics
-- UNION ALL
-- SELECT 'job_notification_history', COUNT(*) FROM iosapp.job_notification_history
-- UNION ALL
-- SELECT 'push_notifications', COUNT(*) FROM iosapp.push_notifications
-- UNION ALL
-- SELECT 'notification_settings', COUNT(*) FROM iosapp.notification_settings
-- UNION ALL
-- SELECT 'notification_delivery_log', COUNT(*) FROM iosapp.notification_delivery_log;

-- ========================================
-- BEGIN TRANSACTION (allows rollback if needed)
-- ========================================

BEGIN;

-- ========================================
-- DELETE OPERATIONS in dependency order
-- ========================================

-- Delete notification delivery logs
DELETE FROM iosapp.notification_delivery_log;
SELECT 'Deleted notification_delivery_log:', ROW_COUNT();

-- Delete push notifications
DELETE FROM iosapp.push_notifications;
SELECT 'Deleted push_notifications:', ROW_COUNT();

-- Delete notification settings
DELETE FROM iosapp.notification_settings;
SELECT 'Deleted notification_settings:', ROW_COUNT();

-- Delete job notification history
DELETE FROM iosapp.job_notification_history;
SELECT 'Deleted job_notification_history:', ROW_COUNT();

-- Delete device tokens
DELETE FROM iosapp.device_tokens;
SELECT 'Deleted device_tokens:', ROW_COUNT();

-- Delete user analytics
DELETE FROM iosapp.user_analytics;
SELECT 'Deleted user_analytics:', ROW_COUNT();

-- Delete job applications
DELETE FROM iosapp.job_applications;
SELECT 'Deleted job_applications:', ROW_COUNT();

-- Delete job views
DELETE FROM iosapp.job_views;
SELECT 'Deleted job_views:', ROW_COUNT();

-- Delete saved jobs
DELETE FROM iosapp.saved_jobs;
SELECT 'Deleted saved_jobs:', ROW_COUNT();

-- Delete users (parent table)
DELETE FROM iosapp.users;
SELECT 'Deleted users:', ROW_COUNT();

-- ========================================
-- VERIFICATION - Check all tables are empty
-- ========================================

SELECT 'AFTER DELETION - Verification:' as status;
SELECT 'users' as table_name, COUNT(*) as remaining_rows FROM iosapp.users
UNION ALL
SELECT 'device_tokens', COUNT(*) FROM iosapp.device_tokens
UNION ALL
SELECT 'saved_jobs', COUNT(*) FROM iosapp.saved_jobs
UNION ALL
SELECT 'job_views', COUNT(*) FROM iosapp.job_views
UNION ALL
SELECT 'job_applications', COUNT(*) FROM iosapp.job_applications
UNION ALL
SELECT 'user_analytics', COUNT(*) FROM iosapp.user_analytics
UNION ALL
SELECT 'job_notification_history', COUNT(*) FROM iosapp.job_notification_history
UNION ALL
SELECT 'push_notifications', COUNT(*) FROM iosapp.push_notifications
UNION ALL
SELECT 'notification_settings', COUNT(*) FROM iosapp.notification_settings
UNION ALL
SELECT 'notification_delivery_log', COUNT(*) FROM iosapp.notification_delivery_log;

-- ========================================
-- COMMIT OR ROLLBACK
-- ========================================

-- Uncomment ONE of the following lines:

-- COMMIT;   -- Uncomment this to make the deletions permanent
-- ROLLBACK; -- Uncomment this to undo all deletions (for testing)

-- ========================================
-- NOTES:
-- ========================================
-- 1. Always run verification queries first
-- 2. Test with ROLLBACK first in a transaction
-- 3. Only COMMIT when you're sure
-- 4. Keep backups of important data
-- 5. Never run this in production!