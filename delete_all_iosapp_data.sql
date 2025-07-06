-- DELETE all data from iosapp schema tables
-- IMPORTANT: This deletes ALL data in development/test environment
-- Execute in correct order to respect foreign key constraints

-- WARNING: This will permanently delete all data!
-- Only run in development/test environments, NEVER in production!

-- ========================================
-- Delete data in dependency order (children first, then parents)
-- ========================================

-- 1. Delete notification delivery logs (no foreign key dependencies)
DELETE FROM iosapp.notification_delivery_log;

-- 2. Delete push notifications (references job_notification_history)
DELETE FROM iosapp.push_notifications;

-- 3. Delete notification settings (references users)
DELETE FROM iosapp.notification_settings;

-- 4. Delete job notification history (references users)
DELETE FROM iosapp.job_notification_history;

-- 5. Delete device tokens (references users)
DELETE FROM iosapp.device_tokens;

-- 6. Delete user analytics (references users)
DELETE FROM iosapp.user_analytics;

-- 7. Delete job applications (references users)
DELETE FROM iosapp.job_applications;

-- 8. Delete job views (references users)
DELETE FROM iosapp.job_views;

-- 9. Delete saved jobs (references users)
DELETE FROM iosapp.saved_jobs;

-- 10. Delete users (parent table)
DELETE FROM iosapp.users;

-- ========================================
-- Optional: Reset sequences if using SERIAL columns
-- ========================================

-- If you have any SERIAL/SEQUENCE columns and want to reset the counters:
-- ALTER SEQUENCE iosapp.users_id_seq RESTART WITH 1;
-- ALTER SEQUENCE iosapp.saved_jobs_id_seq RESTART WITH 1;
-- (Add other sequences as needed)

-- ========================================
-- Verification queries (run after deletion)
-- ========================================

-- Check that all tables are empty:
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