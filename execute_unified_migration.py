#!/usr/bin/env python3
"""
Execute unified users table migration using direct asyncpg connection
"""

import asyncio
import asyncpg
import logging
from datetime import datetime
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def execute_migration_directly():
    """Execute migration using direct asyncpg connection"""
    try:
        logger.info("🚀 Connecting directly to database...")
        
        # Remove asyncpg from URL for direct connection
        db_url = settings.DATABASE_URL.replace("+asyncpg", "")
        
        # Connect directly
        conn = await asyncpg.connect(db_url)
        
        logger.info("📄 Reading migration SQL...")
        with open('/Users/ismatsamadov/birjobBackend/migrations/consolidate_user_tables.sql', 'r') as f:
            migration_sql = f.read()
        
        logger.info("🚀 Executing unified users table migration...")
        
        # Execute the entire migration script
        await conn.execute(migration_sql)
        
        logger.info("✅ Migration schema created successfully!")
        
        # Execute data migration
        logger.info("🔄 Migrating data from old tables...")
        result = await conn.fetchrow("SELECT * FROM iosapp.migrate_user_data()")
        
        if result:
            logger.info(f"✅ Data migration completed:")
            logger.info(f"   - Migrated from users: {result['migrated_from_users']} records")
            logger.info(f"   - Updated from profiles: {result['migrated_from_profiles']} records") 
            logger.info(f"   - Total unified records: {result['total_unified']} records")
        
        # Verify migration
        logger.info("🔍 Verifying migration...")
        
        # Check table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'iosapp' 
                AND table_name = 'users_unified'
            );
        """)
        
        if not table_exists:
            logger.error("❌ users_unified table not found!")
            return False
        
        # Check record count
        record_count = await conn.fetchval("SELECT COUNT(*) FROM iosapp.users_unified")
        logger.info(f"📊 users_unified table has {record_count} records")
        
        # Check sample data
        samples = await conn.fetch("""
            SELECT device_id, first_name, email, match_keywords, profile_completeness
            FROM iosapp.users_unified 
            ORDER BY updated_at DESC 
            LIMIT 3;
        """)
        
        logger.info(f"📋 Sample unified data:")
        for sample in samples:
            keywords = sample['match_keywords'] if sample['match_keywords'] else []
            logger.info(f"   Device: {sample['device_id']}, Name: {sample['first_name']}, Keywords: {keywords}")
        
        await conn.close()
        
        logger.info("🎉 Unified users table deployment completed successfully!")
        logger.info("✅ Ready to update backend code to use iosapp.users_unified!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    logger.info("🚀 Starting unified users table deployment...")
    logger.info(f"⏰ Started at: {datetime.now().isoformat()}")
    
    success = await execute_migration_directly()
    
    if success:
        logger.info("🎉 Deployment completed successfully!")
    else:
        logger.error("❌ Deployment failed!")

if __name__ == "__main__":
    asyncio.run(main())