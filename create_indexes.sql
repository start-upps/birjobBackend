-- =====================================================
-- Create Performance Indexes for iosapp Schema
-- =====================================================

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_device_id ON iosapp.users(device_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON iosapp.users(email) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_active ON iosapp.users(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_users_updated_at ON iosapp.users(updated_at);
CREATE INDEX IF NOT EXISTS idx_users_location ON iosapp.users(location);
CREATE INDEX IF NOT EXISTS idx_users_job_title ON iosapp.users(current_job_title);

-- JSONB indexes for job preferences
CREATE INDEX IF NOT EXISTS idx_users_match_keywords_gin ON iosapp.users USING GIN (match_keywords);
CREATE INDEX IF NOT EXISTS idx_users_skills_gin ON iosapp.users USING GIN (skills);
CREATE INDEX IF NOT EXISTS idx_users_desired_job_types_gin ON iosapp.users USING GIN (desired_job_types);
CREATE INDEX IF NOT EXISTS idx_users_preferred_locations_gin ON iosapp.users USING GIN (preferred_locations);

-- Device tokens indexes
CREATE INDEX IF NOT EXISTS idx_device_tokens_user_id ON iosapp.device_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_device_tokens_active ON iosapp.device_tokens(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_device_tokens_last_seen ON iosapp.device_tokens(last_seen);

-- Job matches indexes
CREATE INDEX IF NOT EXISTS idx_job_matches_user_id ON iosapp.job_matches(user_id);
CREATE INDEX IF NOT EXISTS idx_job_matches_job_id ON iosapp.job_matches(job_id);
CREATE INDEX IF NOT EXISTS idx_job_matches_score ON iosapp.job_matches(match_score DESC);
CREATE INDEX IF NOT EXISTS idx_job_matches_created_at ON iosapp.job_matches(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_matches_unread ON iosapp.job_matches(user_id, is_read) WHERE is_read = FALSE;

-- Keyword subscriptions indexes
CREATE INDEX IF NOT EXISTS idx_keyword_subscriptions_user_id ON iosapp.keyword_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_keyword_subscriptions_active ON iosapp.keyword_subscriptions(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_keyword_subscriptions_keywords_gin ON iosapp.keyword_subscriptions USING GIN (keywords);

-- Saved jobs indexes
CREATE INDEX IF NOT EXISTS idx_saved_jobs_user_id ON iosapp.saved_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_jobs_job_id ON iosapp.saved_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_saved_jobs_status ON iosapp.saved_jobs(application_status);
CREATE INDEX IF NOT EXISTS idx_saved_jobs_created_at ON iosapp.saved_jobs(created_at DESC);

-- Job applications indexes
CREATE INDEX IF NOT EXISTS idx_job_applications_user_id ON iosapp.job_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_job_applications_job_id ON iosapp.job_applications(job_id);
CREATE INDEX IF NOT EXISTS idx_job_applications_status ON iosapp.job_applications(application_status);
CREATE INDEX IF NOT EXISTS idx_job_applications_applied_at ON iosapp.job_applications(applied_at DESC);

-- Job views indexes
CREATE INDEX IF NOT EXISTS idx_job_views_user_id ON iosapp.job_views(user_id);
CREATE INDEX IF NOT EXISTS idx_job_views_job_id ON iosapp.job_views(job_id);
CREATE INDEX IF NOT EXISTS idx_job_views_viewed_at ON iosapp.job_views(viewed_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_views_source ON iosapp.job_views(view_source);

-- Push notifications indexes
CREATE INDEX IF NOT EXISTS idx_push_notifications_user_id ON iosapp.push_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_push_notifications_device_token_id ON iosapp.push_notifications(device_token_id);
CREATE INDEX IF NOT EXISTS idx_push_notifications_status ON iosapp.push_notifications(status);
CREATE INDEX IF NOT EXISTS idx_push_notifications_type ON iosapp.push_notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_push_notifications_created_at ON iosapp.push_notifications(created_at DESC);

-- User analytics indexes
CREATE INDEX IF NOT EXISTS idx_user_analytics_user_id ON iosapp.user_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_user_analytics_profile_strength ON iosapp.user_analytics(profile_strength DESC);
CREATE INDEX IF NOT EXISTS idx_user_analytics_market_fit ON iosapp.user_analytics(market_fit_score DESC);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_users_job_search ON iosapp.users(current_job_title, location, years_of_experience);
CREATE INDEX IF NOT EXISTS idx_users_notifications ON iosapp.users(job_matches_enabled, application_reminders_enabled) WHERE is_active = TRUE;

-- Show index creation summary
SELECT 
    schemaname,
    tablename,
    COUNT(*) as index_count
FROM pg_indexes 
WHERE schemaname = 'iosapp' 
GROUP BY schemaname, tablename
ORDER BY tablename;