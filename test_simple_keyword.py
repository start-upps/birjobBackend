#!/usr/bin/env python3
"""
Simple test for keyword endpoints with detailed error logging
"""

import asyncio
import logging
from app.core.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_operations():
    """Test basic database operations for keywords"""
    
    try:
        # Test 1: Check if table exists
        logger.info("Testing if user_profiles table exists...")
        check_table = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'iosapp' 
                AND table_name = 'user_profiles'
            );
        """
        result = await db_manager.execute_query(check_table)
        table_exists = result[0]['exists']
        logger.info(f"user_profiles table exists: {table_exists}")
        
        if not table_exists:
            logger.error("Table doesn't exist!")
            return False
        
        # Test 2: Create test profile if it doesn't exist
        logger.info("Creating/updating test profile...")
        upsert_profile = """
            INSERT INTO iosapp.user_profiles (device_id, match_keywords, profile_completeness)
            VALUES ($1, $2::jsonb, $3)
            ON CONFLICT (device_id)
            DO UPDATE SET 
                match_keywords = EXCLUDED.match_keywords,
                last_updated = CURRENT_TIMESTAMP
            RETURNING device_id, match_keywords;
        """
        
        import json
        result = await db_manager.execute_query(
            upsert_profile, 
            "test-device-123", 
            json.dumps(["python", "react"]), 
            50
        )
        logger.info(f"Profile created/updated: {result[0] if result else 'No result'}")
        
        # Test 3: Try to get keywords
        logger.info("Testing GET keywords...")
        get_query = """
            SELECT device_id, match_keywords, last_updated
            FROM iosapp.user_profiles 
            WHERE device_id = $1
        """
        
        result = await db_manager.execute_query(get_query, "test-device-123")
        logger.info(f"GET result: {result[0] if result else 'No result'}")
        
        if not result:
            logger.error("No profile found!")
            return False
        
        profile = result[0]
        keywords = profile.get('match_keywords', [])
        logger.info(f"Current keywords: {keywords}")
        
        # Test 4: Update keywords
        logger.info("Testing UPDATE keywords...")
        update_query = """
            UPDATE iosapp.user_profiles 
            SET 
                match_keywords = $1::jsonb,
                last_updated = CURRENT_TIMESTAMP
            WHERE device_id = $2
            RETURNING device_id, match_keywords, last_updated
        """
        
        new_keywords = ["python", "react", "docker"]
        result = await db_manager.execute_query(
            update_query, 
            json.dumps(new_keywords), 
            "test-device-123"
        )
        logger.info(f"UPDATE result: {result[0] if result else 'No result'}")
        
        logger.info("✅ All database operations successful!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database operation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    logger.info("🔍 Testing database operations for keyword endpoints...")
    success = await test_database_operations()
    if success:
        logger.info("🎉 Database operations working correctly!")
    else:
        logger.error("💥 Database operations failed!")

if __name__ == "__main__":
    asyncio.run(main())