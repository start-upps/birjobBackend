-- Fix Missing Foreign Key Relationships in Analytics Schema
-- This addresses critical RDBMS violations where tables reference IDs without proper constraints

-- First, let's check the existing jobs table structure
-- We need to ensure job_id references point to the correct jobs table

-- 1. Add missing foreign keys for job references
-- These tables reference job_id but lack foreign key constraints, violating referential integrity

-- Fix job_engagement table - add FK to jobs table
ALTER TABLE iosapp.job_engagement 
ADD CONSTRAINT fk_job_engagement_job_id 
FOREIGN KEY (job_id) REFERENCES scraper.jobs_jobpost(id) ON DELETE CASCADE;

-- Fix user_actions table - add FK to jobs table  
ALTER TABLE iosapp.user_actions 
ADD CONSTRAINT fk_user_actions_job_id 
FOREIGN KEY (job_id) REFERENCES scraper.jobs_jobpost(id) ON DELETE SET NULL;

-- Fix notification_analytics table - add FK to jobs table
ALTER TABLE iosapp.notification_analytics 
ADD CONSTRAINT fk_notification_analytics_job_id 
FOREIGN KEY (job_id) REFERENCES scraper.jobs_jobpost(id) ON DELETE SET NULL;

-- 2. Add session context to search analytics
-- Currently search_analytics is isolated - needs session relationship
ALTER TABLE iosapp.search_analytics 
ADD COLUMN session_id UUID;

ALTER TABLE iosapp.search_analytics 
ADD CONSTRAINT fk_search_analytics_session_id 
FOREIGN KEY (session_id) REFERENCES iosapp.user_sessions(id) ON DELETE SET NULL;

-- 3. Add session context to job engagement for better analytics
-- This allows tracking which session led to job engagement
ALTER TABLE iosapp.job_engagement 
ADD COLUMN session_id UUID;

ALTER TABLE iosapp.job_engagement 
ADD CONSTRAINT fk_job_engagement_session_id 
FOREIGN KEY (session_id) REFERENCES iosapp.user_sessions(id) ON DELETE SET NULL;

-- 4. Add search reference to user_actions for search-type actions
-- This creates relationship between search analytics and user actions
ALTER TABLE iosapp.user_actions 
ADD COLUMN search_id UUID;

ALTER TABLE iosapp.user_actions 
ADD CONSTRAINT fk_user_actions_search_id 
FOREIGN KEY (search_id) REFERENCES iosapp.search_analytics(id) ON DELETE SET NULL;

-- 5. Add job engagement reference to notification analytics
-- This tracks which notifications led to job engagement
ALTER TABLE iosapp.notification_analytics 
ADD COLUMN job_engagement_id UUID;

ALTER TABLE iosapp.notification_analytics 
ADD CONSTRAINT fk_notification_analytics_job_engagement_id 
FOREIGN KEY (job_engagement_id) REFERENCES iosapp.job_engagement(id) ON DELETE SET NULL;

-- 6. Create indexes for the new foreign key columns
CREATE INDEX IF NOT EXISTS idx_search_analytics_session_id ON iosapp.search_analytics(session_id);
CREATE INDEX IF NOT EXISTS idx_job_engagement_session_id ON iosapp.job_engagement(session_id);
CREATE INDEX IF NOT EXISTS idx_user_actions_search_id ON iosapp.user_actions(search_id) WHERE search_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_notification_analytics_job_engagement_id ON iosapp.notification_analytics(job_engagement_id) WHERE job_engagement_id IS NOT NULL;

-- 7. Update materialized views to include the new relationships
DROP MATERIALIZED VIEW IF EXISTS iosapp.user_engagement_summary;

CREATE MATERIALIZED VIEW iosapp.user_engagement_summary AS
SELECT 
    u.id as user_id,
    u.email,
    u.created_at as user_since,
    COUNT(DISTINCT us.id) as total_sessions,
    SUM(us.duration_seconds) as total_time_spent,
    COUNT(DISTINCT je.job_id) as unique_jobs_viewed,
    COUNT(sj.id) as total_jobs_saved,
    COUNT(DISTINCT sa.id) as total_searches,
    AVG(je.engagement_score) as avg_engagement_score,
    MAX(us.session_start) as last_active,
    -- New metrics with proper relationships
    COUNT(DISTINCT na.id) as total_notifications_received,
    COUNT(DISTINCT CASE WHEN na.opened_at IS NOT NULL THEN na.id END) as notifications_opened,
    COUNT(DISTINCT sa.session_id) as sessions_with_searches,
    COUNT(DISTINCT je.session_id) as sessions_with_job_engagement
FROM iosapp.users u
LEFT JOIN iosapp.user_sessions us ON u.id = us.user_id
LEFT JOIN iosapp.job_engagement je ON u.id = je.user_id
LEFT JOIN iosapp.saved_jobs sj ON u.id = sj.user_id
LEFT JOIN iosapp.search_analytics sa ON u.id = sa.user_id
LEFT JOIN iosapp.notification_analytics na ON u.id = na.user_id
GROUP BY u.id, u.email, u.created_at;

-- 8. Create a comprehensive analytics view that showcases the relationships
CREATE MATERIALIZED VIEW IF NOT EXISTS iosapp.session_analytics_comprehensive AS
SELECT 
    us.id as session_id,
    us.user_id,
    us.session_start,
    us.session_end,
    us.duration_seconds,
    us.actions_count,
    us.jobs_viewed_count,
    us.jobs_saved_count,
    us.searches_performed,
    
    -- Related search analytics (now properly linked)
    COUNT(DISTINCT sa.id) as actual_searches_in_session,
    AVG(sa.results_count) as avg_search_results,
    AVG(sa.clicked_results) as avg_search_clicks,
    
    -- Related job engagement (now properly linked)
    COUNT(DISTINCT je.id) as job_engagements_in_session,
    AVG(je.total_view_time) as avg_job_view_time,
    AVG(je.engagement_score) as avg_engagement_score,
    
    -- Related notifications (through job engagement)
    COUNT(DISTINCT na.id) as notifications_leading_to_session,
    
    -- User actions breakdown
    COUNT(DISTINCT ua.id) as total_actions_recorded,
    COUNT(DISTINCT CASE WHEN ua.action_type = 'search' THEN ua.id END) as search_actions,
    COUNT(DISTINCT CASE WHEN ua.action_type = 'view_job' THEN ua.id END) as job_view_actions,
    COUNT(DISTINCT CASE WHEN ua.action_type = 'save_job' THEN ua.id END) as job_save_actions

FROM iosapp.user_sessions us
LEFT JOIN iosapp.search_analytics sa ON us.id = sa.session_id
LEFT JOIN iosapp.job_engagement je ON us.id = je.session_id
LEFT JOIN iosapp.user_actions ua ON us.id = ua.session_id
LEFT JOIN iosapp.notification_analytics na ON je.id = na.job_engagement_id
WHERE us.session_start >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY us.id, us.user_id, us.session_start, us.session_end, us.duration_seconds, 
         us.actions_count, us.jobs_viewed_count, us.jobs_saved_count, us.searches_performed;

-- Create indexes for the new comprehensive view
CREATE INDEX IF NOT EXISTS idx_session_analytics_comprehensive_session_id ON iosapp.session_analytics_comprehensive(session_id);
CREATE INDEX IF NOT EXISTS idx_session_analytics_comprehensive_user_id ON iosapp.session_analytics_comprehensive(user_id);
CREATE INDEX IF NOT EXISTS idx_session_analytics_comprehensive_session_start ON iosapp.session_analytics_comprehensive(session_start);

-- Summary of foreign key fixes applied:
-- 1. job_engagement.job_id -> scraper.jobs_jobpost.id (CASCADE DELETE)
-- 2. user_actions.job_id -> scraper.jobs_jobpost.id (SET NULL)
-- 3. notification_analytics.job_id -> scraper.jobs_jobpost.id (SET NULL)
-- 4. search_analytics.session_id -> user_sessions.id (SET NULL)
-- 5. job_engagement.session_id -> user_sessions.id (SET NULL)  
-- 6. user_actions.search_id -> search_analytics.id (SET NULL)
-- 7. notification_analytics.job_engagement_id -> job_engagement.id (SET NULL)
--
-- This creates a properly normalized analytics schema with full referential integrity
-- and enables comprehensive cross-table analytics queries following RDBMS principles.