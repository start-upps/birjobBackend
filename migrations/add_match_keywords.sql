-- Migration: Add match_keywords column to user profiles
-- This migration adds profile-based keyword matching functionality

-- Add match_keywords JSONB column to user_profiles table
ALTER TABLE iosapp.user_profiles 
ADD COLUMN IF NOT EXISTS match_keywords JSONB DEFAULT '[]'::jsonb;

-- Create index for better performance on keyword queries
CREATE INDEX IF NOT EXISTS idx_user_profiles_match_keywords 
ON iosapp.user_profiles USING GIN (match_keywords);

-- Add comment for documentation
COMMENT ON COLUMN iosapp.user_profiles.match_keywords IS 'User-defined keywords for job matching stored as JSONB array';

-- Create function to extract keywords for matching
CREATE OR REPLACE FUNCTION iosapp.extract_user_match_keywords(user_id UUID)
RETURNS TEXT[] AS $$
BEGIN
    RETURN (
        SELECT ARRAY(
            SELECT jsonb_array_elements_text(match_keywords)
            FROM iosapp.user_profiles 
            WHERE user_id = extract_user_match_keywords.user_id
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Create function to update match keywords
CREATE OR REPLACE FUNCTION iosapp.update_user_match_keywords(
    p_user_id UUID,
    p_keywords TEXT[]
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE iosapp.user_profiles 
    SET 
        match_keywords = to_jsonb(p_keywords),
        last_updated = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Create enhanced job matching view with profile keywords
CREATE OR REPLACE VIEW iosapp.v_enhanced_job_matches AS
SELECT 
    jp.id as job_id,
    jp.title,
    jp.company,
    jp.location,
    jp.description,
    jp.requirements,
    jp.salary,
    jp.source,
    jp.created_at,
    up.user_id,
    up.device_id,
    up.match_keywords,
    iosapp.extract_user_match_keywords(up.user_id) as keyword_array,
    -- Calculate basic match score based on keyword presence
    CASE 
        WHEN up.match_keywords IS NULL OR jsonb_array_length(up.match_keywords) = 0 THEN 0
        ELSE (
            SELECT COUNT(*)::FLOAT / jsonb_array_length(up.match_keywords) * 100
            FROM (
                SELECT jsonb_array_elements_text(up.match_keywords) as keyword
            ) keywords
            WHERE jp.title ILIKE '%' || keyword || '%' 
               OR jp.description ILIKE '%' || keyword || '%'
               OR jp.requirements ILIKE '%' || keyword || '%'
        )
    END as basic_match_score
FROM scraper.jobs_jobpost jp
CROSS JOIN iosapp.user_profiles up
WHERE up.match_keywords IS NOT NULL 
  AND jsonb_array_length(up.match_keywords) > 0;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_jobs_jobpost_title_gin 
ON scraper.jobs_jobpost USING GIN (to_tsvector('english', title));

CREATE INDEX IF NOT EXISTS idx_jobs_jobpost_description_gin 
ON scraper.jobs_jobpost USING GIN (to_tsvector('english', description));

CREATE INDEX IF NOT EXISTS idx_jobs_jobpost_requirements_gin 
ON scraper.jobs_jobpost USING GIN (to_tsvector('english', requirements));

-- Migration log
INSERT INTO iosapp.migration_log (migration_name, applied_at, description)
VALUES (
    'add_match_keywords_v1',
    CURRENT_TIMESTAMP,
    'Added match_keywords JSONB column and supporting functions for profile-based keyword matching'
) ON CONFLICT (migration_name) DO NOTHING;