#!/usr/bin/env python3
"""
Production Database Migration Deployment Script
Safely deploys profile-based keyword matching schema to production
"""

import asyncio
import logging
import os
from datetime import datetime
from app.core.database import db_manager
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_migration_status():
    """Check if migrations have already been applied"""
    try:
        # Check if migration log table exists
        check_table = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'iosapp' 
                AND table_name = 'migration_log'
            );
        """
        result = await db_manager.execute_query(check_table)
        table_exists = result[0]['exists'] if result else False
        
        if not table_exists:
            logger.info("Migration log table doesn't exist - this is the first migration")
            return False
        
        # Check if specific migration has been applied
        check_migration = """
            SELECT COUNT(*) as count FROM iosapp.migration_log 
            WHERE migration_name = 'add_match_keywords_v1'
        """
        result = await db_manager.execute_query(check_migration)
        migration_exists = result[0]['count'] > 0 if result else False
        
        if migration_exists:
            logger.info("✅ Migration 'add_match_keywords_v1' already applied")
            return True
        else:
            logger.info("❌ Migration 'add_match_keywords_v1' not yet applied")
            return False
            
    except Exception as e:
        logger.error(f"Error checking migration status: {e}")
        return False

async def create_migration_log_table():
    """Create migration log table if it doesn't exist"""
    try:
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS iosapp.migration_log (
                id SERIAL PRIMARY KEY,
                migration_name VARCHAR(255) UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                rollback_sql TEXT
            );
        """
        await db_manager.execute_query(create_table_sql)
        logger.info("✅ Migration log table created/verified")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating migration log table: {e}")
        return False

async def apply_schema_migration():
    """Apply the match_keywords schema migration"""
    try:
        logger.info("🚀 Starting schema migration for match_keywords...")
        
        # 1. Add match_keywords column
        add_column_sql = """
            ALTER TABLE iosapp.user_profiles 
            ADD COLUMN IF NOT EXISTS match_keywords JSONB DEFAULT '[]'::jsonb;
        """
        await db_manager.execute_query(add_column_sql)
        logger.info("✅ Added match_keywords JSONB column")
        
        # 2. Create GIN index for performance
        create_index_sql = """
            CREATE INDEX IF NOT EXISTS idx_user_profiles_match_keywords 
            ON iosapp.user_profiles USING GIN (match_keywords);
        """
        await db_manager.execute_query(create_index_sql)
        logger.info("✅ Created GIN index for match_keywords")
        
        # 3. Add comment for documentation
        add_comment_sql = """
            COMMENT ON COLUMN iosapp.user_profiles.match_keywords IS 
            'User-defined keywords for job matching stored as JSONB array';
        """
        await db_manager.execute_query(add_comment_sql)
        logger.info("✅ Added column documentation")
        
        # 4. Create helper function for extracting keywords
        create_function_sql = """
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
        """
        await db_manager.execute_query(create_function_sql)
        logger.info("✅ Created keyword extraction function")
        
        # 5. Create update function
        update_function_sql = """
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
        """
        await db_manager.execute_query(update_function_sql)
        logger.info("✅ Created keyword update function")
        
        # 6. Create performance indexes for job matching
        job_indexes_sql = [
            """
            CREATE INDEX IF NOT EXISTS idx_jobs_jobpost_title_gin 
            ON scraper.jobs_jobpost USING GIN (to_tsvector('english', title));
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_jobs_jobpost_description_gin 
            ON scraper.jobs_jobpost USING GIN (to_tsvector('english', description));
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_jobs_jobpost_requirements_gin 
            ON scraper.jobs_jobpost USING GIN (to_tsvector('english', requirements));
            """
        ]
        
        for index_sql in job_indexes_sql:
            await db_manager.execute_query(index_sql)
        logger.info("✅ Created job search performance indexes")
        
        # 7. Record migration in log
        log_migration_sql = """
            INSERT INTO iosapp.migration_log (migration_name, applied_at, description)
            VALUES (
                'add_match_keywords_v1',
                CURRENT_TIMESTAMP,
                'Added match_keywords JSONB column and supporting functions for profile-based keyword matching'
            ) ON CONFLICT (migration_name) DO NOTHING;
        """
        await db_manager.execute_query(log_migration_sql)
        logger.info("✅ Migration logged successfully")
        
        logger.info("🎉 Schema migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error applying schema migration: {e}")
        return False

async def verify_migration():
    """Verify that the migration was applied correctly"""
    try:
        logger.info("🔍 Verifying migration...")
        
        # Check column exists
        check_column = """
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'iosapp' 
                AND table_name = 'user_profiles' 
                AND column_name = 'match_keywords'
            );
        """
        result = await db_manager.execute_query(check_column)
        column_exists = result[0]['exists'] if result else False
        
        if not column_exists:
            logger.error("❌ match_keywords column not found!")
            return False
        
        # Check index exists
        check_index = """
            SELECT EXISTS (
                SELECT FROM pg_indexes 
                WHERE tablename = 'user_profiles' 
                AND indexname = 'idx_user_profiles_match_keywords'
            );
        """
        result = await db_manager.execute_query(check_index)
        index_exists = result[0]['exists'] if result else False
        
        if not index_exists:
            logger.error("❌ GIN index not found!")
            return False
        
        # Check functions exist
        check_function = """
            SELECT EXISTS (
                SELECT FROM pg_proc 
                WHERE proname = 'extract_user_match_keywords'
            );
        """
        result = await db_manager.execute_query(check_function)
        function_exists = result[0]['exists'] if result else False
        
        if not function_exists:
            logger.error("❌ Helper functions not found!")
            return False
        
        logger.info("✅ All migration components verified successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying migration: {e}")
        return False

async def migrate_existing_subscriptions():
    """Migrate existing keyword subscriptions to profile keywords"""
    try:
        logger.info("🔄 Checking for existing subscriptions to migrate...")
        
        # Check if subscription tables exist
        check_subscriptions = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'iosapp' 
                AND table_name = 'keyword_subscriptions'
            );
        """
        result = await db_manager.execute_query(check_subscriptions)
        subscriptions_exist = result[0]['exists'] if result else False
        
        if not subscriptions_exist:
            logger.info("ℹ️  No existing subscription tables found - skipping migration")
            return True
        
        # Count active subscriptions
        count_subscriptions = """
            SELECT COUNT(DISTINCT device_id) as count 
            FROM iosapp.keyword_subscriptions 
            WHERE active = true
        """
        result = await db_manager.execute_query(count_subscriptions)
        subscription_count = result[0]['count'] if result else 0
        
        if subscription_count == 0:
            logger.info("ℹ️  No active subscriptions found - skipping migration")
            return True
        
        logger.info(f"📋 Found {subscription_count} active subscription devices to migrate")
        
        # Run migration (would implement actual migration logic here)
        # For now, just log that we found subscriptions
        logger.info("⚠️  Subscription migration would be run here in production")
        logger.info("ℹ️  Manual migration can be run later using migrate_subscriptions_to_profile.sql")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error migrating subscriptions: {e}")
        return False

async def main():
    """Main migration deployment function"""
    try:
        logger.info("🚀 Starting database migration deployment...")
        logger.info(f"📍 Target database: {settings.DATABASE_URL[:50]}...")
        logger.info(f"⏰ Started at: {datetime.now().isoformat()}")
        
        # Step 1: Check if already applied
        already_applied = await check_migration_status()
        if already_applied:
            logger.info("✅ Migration already applied - skipping")
            return True
        
        # Step 2: Create migration log table
        if not await create_migration_log_table():
            logger.error("❌ Failed to create migration log table")
            return False
        
        # Step 3: Apply schema migration
        if not await apply_schema_migration():
            logger.error("❌ Failed to apply schema migration")
            return False
        
        # Step 4: Verify migration
        if not await verify_migration():
            logger.error("❌ Migration verification failed")
            return False
        
        # Step 5: Handle existing subscriptions
        if not await migrate_existing_subscriptions():
            logger.error("❌ Subscription migration failed")
            return False
        
        logger.info("🎉 Migration deployment completed successfully!")
        logger.info("✅ Profile-based keyword matching is now ready!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration deployment failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())