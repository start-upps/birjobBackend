-- Individual DELETE commands for iosapp schema tables
-- Use these when you need to delete data from specific tables only

-- ========================================
-- NOTIFICATION SYSTEM TABLES
-- ========================================

-- Delete notification delivery logs
DELETE FROM iosapp.notification_delivery_log;

-- Delete push notifications 
DELETE FROM iosapp.push_notifications;

-- Delete notification settings
DELETE FROM iosapp.notification_settings;

-- Delete job notification history
DELETE FROM iosapp.job_notification_history;

-- ========================================
-- DEVICE AND USER MANAGEMENT
-- ========================================

-- Delete device tokens
DELETE FROM iosapp.device_tokens;

-- Delete users (WARNING: This will cascade to related tables if FK constraints exist)
DELETE FROM iosapp.users;

-- ========================================
-- JOB INTERACTION TABLES
-- ========================================

-- Delete job applications
DELETE FROM iosapp.job_applications;

-- Delete job views (analytics)
DELETE FROM iosapp.job_views;

-- Delete saved jobs
DELETE FROM iosapp.saved_jobs;

-- ========================================
-- ANALYTICS TABLES
-- ========================================

-- Delete user analytics
DELETE FROM iosapp.user_analytics;

-- ========================================
-- CONDITIONAL DELETES (with WHERE clauses)
-- ========================================

-- Delete old notification history (older than 30 days)
-- DELETE FROM iosapp.job_notification_history 
-- WHERE notification_sent_at < NOW() - INTERVAL '30 days';

-- Delete inactive device tokens
-- DELETE FROM iosapp.device_tokens 
-- WHERE is_active = false;

-- Delete users with no activity (no saved jobs, views, or applications)
-- DELETE FROM iosapp.users 
-- WHERE id NOT IN (
--     SELECT DISTINCT user_id FROM iosapp.saved_jobs WHERE user_id IS NOT NULL
--     UNION
--     SELECT DISTINCT user_id FROM iosapp.job_views WHERE user_id IS NOT NULL
--     UNION
--     SELECT DISTINCT user_id FROM iosapp.job_applications WHERE user_id IS NOT NULL
-- );

-- Delete old analytics data
-- DELETE FROM iosapp.user_analytics 
-- WHERE created_at < NOW() - INTERVAL '90 days';

-- ========================================
-- TEST DATA SPECIFIC DELETES
-- ========================================

-- Delete test users (assuming test emails contain 'test')
-- DELETE FROM iosapp.users 
-- WHERE email LIKE '%test%' OR email LIKE '%example.com';

-- Delete test device tokens
-- DELETE FROM iosapp.device_tokens 
-- WHERE device_id LIKE 'test-%' OR device_id LIKE 'TEST-%';

-- Delete notifications for test users
-- DELETE FROM iosapp.job_notification_history 
-- WHERE user_id IN (
--     SELECT id FROM iosapp.users 
--     WHERE email LIKE '%test%' OR email LIKE '%example.com'
-- );

-- ========================================
-- VERIFICATION QUERIES
-- ========================================

-- Count remaining rows in each table
-- SELECT 
--     'users' as table_name, 
--     COUNT(*) as row_count 
-- FROM iosapp.users
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