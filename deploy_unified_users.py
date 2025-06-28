#!/usr/bin/env python3
"""
Deploy unified users table migration
"""

import asyncio
import logging
from datetime import datetime
from app.core.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def execute_migration():
    """Execute the unified users table migration"""
    try:
        logger.info("🚀 Starting unified users table migration...")
        
        # Read migration SQL
        with open('/Users/ismatsamadov/birjobBackend/migrations/consolidate_user_tables.sql', 'r') as f:
            migration_sql = f.read()
        
        # Execute as single script to handle dollar-quoted functions
        logger.info("📄 Executing migration as single script...")
        await db_manager.execute_query(migration_sql)
        
        logger.info("✅ Migration schema created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

async def migrate_data():
    """Migrate data from old tables to unified table"""
    try:
        logger.info("🔄 Migrating data from old tables...")
        
        # Execute data migration function
        migration_result = await db_manager.execute_query("SELECT * FROM iosapp.migrate_user_data()")
        
        if migration_result:
            result = migration_result[0]
            logger.info(f"✅ Data migration completed:")
            logger.info(f"   - Migrated from users: {result['migrated_from_users']} records")
            logger.info(f"   - Updated from profiles: {result['migrated_from_profiles']} records")
            logger.info(f"   - Total unified records: {result['total_unified']} records")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Data migration failed: {e}")
        return False

async def verify_migration():
    """Verify the migration was successful"""
    try:
        logger.info("🔍 Verifying migration...")
        
        # Check table exists
        table_check = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'iosapp' 
                AND table_name = 'users_unified'
            );
        """
        table_exists = await db_manager.execute_query(table_check)
        
        if not table_exists[0]['exists']:
            logger.error("❌ users_unified table not found!")
            return False
        
        # Check record count
        count_query = "SELECT COUNT(*) as count FROM iosapp.users_unified"
        count_result = await db_manager.execute_query(count_query)
        record_count = count_result[0]['count']
        
        logger.info(f"📊 users_unified table has {record_count} records")
        
        # Check indexes
        index_check = """
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'users_unified' 
            AND schemaname = 'iosapp'
            ORDER BY indexname;
        """
        indexes = await db_manager.execute_query(index_check)
        logger.info(f"📇 Created {len(indexes)} indexes:")
        for idx in indexes:
            logger.info(f"   - {idx['indexname']}")
        
        # Check functions
        function_check = """
            SELECT proname FROM pg_proc 
            WHERE proname IN ('get_user_keywords', 'update_user_keywords', 'calculate_unified_profile_completeness')
            ORDER BY proname;
        """
        functions = await db_manager.execute_query(function_check)
        logger.info(f"🔧 Created {len(functions)} helper functions:")
        for func in functions:
            logger.info(f"   - {func['proname']}")
        
        # Sample data verification
        sample_query = """
            SELECT device_id, first_name, email, match_keywords, profile_completeness, updated_at
            FROM iosapp.users_unified 
            ORDER BY updated_at DESC 
            LIMIT 3;
        """
        samples = await db_manager.execute_query(sample_query)
        logger.info(f"📋 Sample unified data:")
        for sample in samples:
            logger.info(f"   Device: {sample['device_id']}, Name: {sample['first_name']}, Keywords: {sample['match_keywords']}")
        
        logger.info("✅ Migration verification successful!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

async def main():
    """Main migration function"""
    try:
        logger.info("🚀 Starting unified users table deployment...")
        logger.info(f"⏰ Started at: {datetime.now().isoformat()}")
        
        # Step 1: Execute migration schema
        if not await execute_migration():
            logger.error("❌ Schema migration failed")
            return False
        
        # Step 2: Migrate data
        if not await migrate_data():
            logger.error("❌ Data migration failed") 
            return False
        
        # Step 3: Verify migration
        if not await verify_migration():
            logger.error("❌ Migration verification failed")
            return False
        
        logger.info("🎉 Unified users table deployment completed successfully!")
        logger.info("✅ Ready to update backend code to use iosapp.users_unified!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())