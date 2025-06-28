-- Migration: Convert keyword subscriptions to profile-based matching
-- This migration safely transfers existing keyword subscriptions to user profiles

-- Step 1: Create migration tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS iosapp.migration_log (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    rollback_sql TEXT
);

-- Step 2: Backup existing subscriptions before migration
CREATE TABLE IF NOT EXISTS iosapp.keyword_subscriptions_backup AS
SELECT * FROM iosapp.keyword_subscriptions;

-- Step 3: Create function to migrate subscriptions to profiles
CREATE OR REPLACE FUNCTION iosapp.migrate_subscriptions_to_profiles()
RETURNS TABLE(
    device_id VARCHAR,
    old_keywords TEXT[],
    new_keywords JSONB,
    migration_status TEXT
) AS $$
DECLARE
    subscription_record RECORD;
    current_profile RECORD;
    merged_keywords TEXT[];
    keywords_json JSONB;
BEGIN
    -- Process each active subscription
    FOR subscription_record IN 
        SELECT 
            ks.device_id,
            ARRAY_AGG(DISTINCT k.keyword) as keywords
        FROM iosapp.keyword_subscriptions ks
        JOIN iosapp.keywords k ON ks.subscription_id = k.subscription_id
        WHERE ks.active = true
        GROUP BY ks.device_id
    LOOP
        -- Get current profile keywords if any
        SELECT match_keywords INTO current_profile
        FROM iosapp.user_profiles 
        WHERE user_profiles.device_id = subscription_record.device_id;
        
        -- Merge existing profile keywords with subscription keywords
        merged_keywords := subscription_record.keywords;
        
        IF current_profile.match_keywords IS NOT NULL THEN
            -- Convert existing JSONB to array and merge
            SELECT ARRAY(
                SELECT DISTINCT unnest(
                    ARRAY(SELECT jsonb_array_elements_text(current_profile.match_keywords)) ||
                    subscription_record.keywords
                )
            ) INTO merged_keywords;
        END IF;
        
        -- Convert to JSONB
        keywords_json := to_jsonb(merged_keywords);
        
        -- Update or create user profile with merged keywords
        INSERT INTO iosapp.user_profiles (
            user_id, 
            device_id, 
            match_keywords, 
            created_at, 
            last_updated
        )
        VALUES (
            gen_random_uuid(),
            subscription_record.device_id,
            keywords_json,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (device_id) 
        DO UPDATE SET 
            match_keywords = keywords_json,
            last_updated = CURRENT_TIMESTAMP;
        
        -- Return migration result
        device_id := subscription_record.device_id;
        old_keywords := subscription_record.keywords;
        new_keywords := keywords_json;
        migration_status := 'SUCCESS';
        
        RETURN NEXT;
    END LOOP;
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Step 4: Run the migration
DO $$
DECLARE
    migration_count INTEGER;
    migration_results RECORD;
BEGIN
    -- Check if migration has already been run
    IF EXISTS (
        SELECT 1 FROM iosapp.migration_log 
        WHERE migration_name = 'migrate_subscriptions_to_profiles_v1'
    ) THEN
        RAISE NOTICE 'Migration already completed. Skipping...';
        RETURN;
    END IF;
    
    -- Count subscriptions to migrate
    SELECT COUNT(DISTINCT device_id) INTO migration_count
    FROM iosapp.keyword_subscriptions 
    WHERE active = true;
    
    RAISE NOTICE 'Starting migration of % device subscriptions to profile keywords...', migration_count;
    
    -- Run migration and log results
    FOR migration_results IN 
        SELECT * FROM iosapp.migrate_subscriptions_to_profiles()
    LOOP
        RAISE NOTICE 'Migrated device %: % keywords -> %', 
            migration_results.device_id,
            array_length(migration_results.old_keywords, 1),
            jsonb_array_length(migration_results.new_keywords);
    END LOOP;
    
    -- Mark migration as complete
    INSERT INTO iosapp.migration_log (
        migration_name, 
        applied_at, 
        description,
        rollback_sql
    ) VALUES (
        'migrate_subscriptions_to_profiles_v1',
        CURRENT_TIMESTAMP,
        FORMAT('Successfully migrated %s subscription devices to profile-based keywords', migration_count),
        'UPDATE iosapp.user_profiles SET match_keywords = NULL; DELETE FROM iosapp.migration_log WHERE migration_name = ''migrate_subscriptions_to_profiles_v1'';'
    );
    
    RAISE NOTICE 'Migration completed successfully!';
END;
$$;

-- Step 5: Create view for migration verification
CREATE OR REPLACE VIEW iosapp.v_migration_verification AS
SELECT 
    up.device_id,
    up.match_keywords,
    jsonb_array_length(up.match_keywords) as keyword_count,
    (
        SELECT COUNT(*) 
        FROM iosapp.keyword_subscriptions ks 
        WHERE ks.device_id = up.device_id AND ks.active = true
    ) as old_subscription_count,
    up.last_updated as migrated_at
FROM iosapp.user_profiles up
WHERE up.match_keywords IS NOT NULL
ORDER BY up.last_updated DESC;

-- Step 6: Create function to safely deactivate old subscriptions (optional)
CREATE OR REPLACE FUNCTION iosapp.deactivate_migrated_subscriptions()
RETURNS INTEGER AS $$
DECLARE
    deactivated_count INTEGER := 0;
BEGIN
    -- Only deactivate subscriptions where profile migration exists
    UPDATE iosapp.keyword_subscriptions 
    SET 
        active = false,
        deactivated_reason = 'Migrated to profile-based matching',
        last_updated = CURRENT_TIMESTAMP
    WHERE device_id IN (
        SELECT device_id 
        FROM iosapp.user_profiles 
        WHERE match_keywords IS NOT NULL 
        AND jsonb_array_length(match_keywords) > 0
    ) AND active = true;
    
    GET DIAGNOSTICS deactivated_count = ROW_COUNT;
    
    RAISE NOTICE 'Deactivated % legacy subscriptions', deactivated_count;
    
    RETURN deactivated_count;
END;
$$ LANGUAGE plpgsql;

-- Step 7: Performance optimizations for new system
-- Index for fast profile keyword lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_match_keywords_gin 
ON iosapp.user_profiles USING GIN (match_keywords);

-- Index for device-based lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_device_id 
ON iosapp.user_profiles (device_id);

-- Index for active subscription tracking (for gradual migration)
CREATE INDEX IF NOT EXISTS idx_keyword_subscriptions_active_device 
ON iosapp.keyword_subscriptions (device_id, active, last_updated);

-- Step 8: Create monitoring query for system health
CREATE OR REPLACE VIEW iosapp.v_matching_system_health AS
SELECT 
    'Profile-based Matching' as system_type,
    COUNT(*) as active_users,
    AVG(jsonb_array_length(match_keywords)) as avg_keywords_per_user,
    SUM(jsonb_array_length(match_keywords)) as total_keywords
FROM iosapp.user_profiles 
WHERE match_keywords IS NOT NULL 
AND jsonb_array_length(match_keywords) > 0

UNION ALL

SELECT 
    'Legacy Subscriptions' as system_type,
    COUNT(DISTINCT device_id) as active_users,
    AVG(keyword_count) as avg_keywords_per_user,
    SUM(keyword_count) as total_keywords
FROM (
    SELECT 
        ks.device_id,
        COUNT(k.keyword) as keyword_count
    FROM iosapp.keyword_subscriptions ks
    JOIN iosapp.keywords k ON ks.subscription_id = k.subscription_id
    WHERE ks.active = true
    GROUP BY ks.device_id
) legacy_stats;

-- Final verification query
SELECT 
    'Migration Summary' as report_type,
    (SELECT COUNT(*) FROM iosapp.v_migration_verification) as profiles_with_keywords,
    (SELECT COUNT(DISTINCT device_id) FROM iosapp.keyword_subscriptions WHERE active = true) as active_legacy_subscriptions,
    (SELECT applied_at FROM iosapp.migration_log WHERE migration_name = 'migrate_subscriptions_to_profiles_v1') as migration_date;

-- Usage instructions
/*
Post-migration steps:

1. Verify migration:
   SELECT * FROM iosapp.v_migration_verification LIMIT 10;

2. Check system health:
   SELECT * FROM iosapp.v_matching_system_health;

3. Optional: Deactivate legacy subscriptions after testing
   SELECT iosapp.deactivate_migrated_subscriptions();

4. Test new profile-based matching:
   - Use new API endpoints: GET /api/v1/users/{device_id}/profile/keywords
   - Test matching: GET /api/v1/users/{device_id}/profile/matches

5. Monitor performance:
   - Check query execution times
   - Monitor keyword match effectiveness
   - Verify user experience improvements
*/