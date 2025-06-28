#!/usr/bin/env python3
"""
Analyze current table structures for consolidation
"""

import asyncio
import logging
from app.core.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_table_structures():
    """Analyze both user tables"""
    
    try:
        # Check users table structure
        logger.info("📊 Analyzing iosapp.users table...")
        users_structure = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'iosapp' 
            AND table_name = 'users'
            ORDER BY ordinal_position;
        """
        users_columns = await db_manager.execute_query(users_structure)
        
        logger.info(f"Users table has {len(users_columns)} columns:")
        for col in users_columns:
            logger.info(f"  {col['column_name']}: {col['data_type']} {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
        
        # Check user_profiles table structure  
        logger.info("\n📊 Analyzing iosapp.user_profiles table...")
        profiles_structure = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'iosapp' 
            AND table_name = 'user_profiles'
            ORDER BY ordinal_position;
        """
        profiles_columns = await db_manager.execute_query(profiles_structure)
        
        logger.info(f"User_profiles table has {len(profiles_columns)} columns:")
        for col in profiles_columns:
            logger.info(f"  {col['column_name']}: {col['data_type']} {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
        
        # Count records in each table
        logger.info("\n📈 Analyzing data...")
        
        users_count = await db_manager.execute_query("SELECT COUNT(*) as count FROM iosapp.users")
        profiles_count = await db_manager.execute_query("SELECT COUNT(*) as count FROM iosapp.user_profiles")
        
        logger.info(f"Users table: {users_count[0]['count']} records")
        logger.info(f"User_profiles table: {profiles_count[0]['count']} records")
        
        # Check for common device_ids
        common_devices = """
            SELECT COUNT(*) as count 
            FROM iosapp.users u 
            INNER JOIN iosapp.user_profiles p ON u.device_id = p.device_id
        """
        common_count = await db_manager.execute_query(common_devices)
        logger.info(f"Common device_ids: {common_count[0]['count']} records")
        
        # Sample data from both tables
        logger.info("\n📋 Sample data from users table:")
        sample_users = await db_manager.execute_query("SELECT device_id, first_name, email, created_at FROM iosapp.users LIMIT 3")
        for user in sample_users:
            logger.info(f"  Device: {user['device_id']}, Name: {user['first_name']}, Email: {user['email']}")
        
        logger.info("\n📋 Sample data from user_profiles table:")
        sample_profiles = await db_manager.execute_query("SELECT device_id, match_keywords, created_at FROM iosapp.user_profiles LIMIT 3")
        for profile in sample_profiles:
            logger.info(f"  Device: {profile['device_id']}, Keywords: {profile['match_keywords']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        return False

async def main():
    logger.info("🔍 Analyzing user table structures for consolidation...")
    success = await analyze_table_structures()
    if success:
        logger.info("✅ Analysis completed!")
    else:
        logger.error("❌ Analysis failed!")

if __name__ == "__main__":
    asyncio.run(main())