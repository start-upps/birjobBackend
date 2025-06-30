-- =====================================================
-- Data Migration Script for iosapp schema
-- =====================================================

-- Migrate users_unified data to new users table
INSERT INTO iosapp.users (
    device_id, first_name, last_name, email, phone, location, current_job_title,
    years_of_experience, linkedin_profile, portfolio_url, bio,
    desired_job_types, remote_work_preference, skills, preferred_locations, match_keywords,
    min_salary, max_salary, salary_currency, salary_negotiable,
    job_matches_enabled, application_reminders_enabled, weekly_digest_enabled,
    market_insights_enabled, quiet_hours_enabled, 
    quiet_hours_start, quiet_hours_end, preferred_notification_time,
    profile_visibility, share_analytics, share_job_view_history, allow_personalized_recommendations,
    additional_personal_info, additional_job_preferences,
    additional_notification_settings, additional_privacy_settings,
    profile_completeness, created_at, updated_at
)
SELECT 
    device_id, first_name, last_name, email, phone, location, current_job_title,
    CASE 
        WHEN years_of_experience ~ '^[0-9]+$' THEN years_of_experience::integer 
        ELSE NULL 
    END as years_of_experience,
    linkedin_profile, portfolio_url, bio,
    COALESCE(desired_job_types, '[]'::jsonb), 
    COALESCE(remote_work_preference, 'hybrid'),
    COALESCE(skills, '[]'::jsonb), 
    COALESCE(preferred_locations, '[]'::jsonb), 
    COALESCE(match_keywords, '[]'::jsonb),
    min_salary, max_salary, 
    COALESCE(salary_currency, 'USD'),
    COALESCE(salary_negotiable, TRUE),
    COALESCE(job_matches_enabled, TRUE),
    COALESCE(application_reminders_enabled, TRUE),
    COALESCE(weekly_digest_enabled, FALSE),
    COALESCE(market_insights_enabled, TRUE),
    COALESCE(quiet_hours_enabled, TRUE),
    CASE 
        WHEN quiet_hours_start ~ '^[0-9]{2}:[0-9]{2}$' THEN quiet_hours_start::time
        ELSE '22:00'::time 
    END,
    CASE 
        WHEN quiet_hours_end ~ '^[0-9]{2}:[0-9]{2}$' THEN quiet_hours_end::time
        ELSE '08:00'::time 
    END,
    CASE 
        WHEN preferred_notification_time ~ '^[0-9]{2}:[0-9]{2}$' THEN preferred_notification_time::time
        ELSE '09:00'::time 
    END,
    COALESCE(profile_visibility, 'private'),
    COALESCE(share_analytics, FALSE),
    COALESCE(share_job_view_history, FALSE),
    COALESCE(allow_personalized_recommendations, TRUE),
    COALESCE(additional_personal_info, '{}'::jsonb),
    COALESCE(additional_job_preferences, '{}'::jsonb),
    COALESCE(additional_notification_settings, '{}'::jsonb),
    COALESCE(additional_privacy_settings, '{}'::jsonb),
    COALESCE(profile_completeness, 0),
    created_at, updated_at
FROM iosapp.users_unified
ON CONFLICT (device_id) DO NOTHING;

-- Create device tokens for each user (linking users to their device_id)
INSERT INTO iosapp.device_tokens (user_id, device_token, device_type, device_info, is_active)
SELECT 
    u.id,
    u.device_id,
    'iOS',
    '{}'::jsonb,
    TRUE
FROM iosapp.users u
ON CONFLICT (device_token) DO NOTHING;

-- Migrate keyword subscriptions from match_keywords in users table
INSERT INTO iosapp.keyword_subscriptions (user_id, keywords, location_filters, source_filters, is_active)
SELECT 
    u.id,
    u.match_keywords,
    '{}'::jsonb,
    '[]'::jsonb,
    TRUE
FROM iosapp.users u
WHERE jsonb_array_length(u.match_keywords) > 0;

-- Initialize user analytics for all users
INSERT INTO iosapp.user_analytics (user_id)
SELECT id FROM iosapp.users
ON CONFLICT (user_id) DO NOTHING;

-- Show migration results
SELECT 
    'Migration Complete' as status,
    (SELECT COUNT(*) FROM iosapp.users) as migrated_users,
    (SELECT COUNT(*) FROM iosapp.device_tokens) as migrated_devices,
    (SELECT COUNT(*) FROM iosapp.keyword_subscriptions) as migrated_keywords,
    (SELECT COUNT(*) FROM iosapp.user_analytics) as migrated_analytics;