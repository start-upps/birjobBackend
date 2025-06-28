#!/usr/bin/env python3
"""
Create user_profiles table and apply keyword matching schema
"""

import asyncio
import logging
from app.core.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_user_profiles_table():
    """Create the user_profiles table with match_keywords support"""
    try:
        logger.info("🚀 Creating user_profiles table...")
        
        # Create user_profiles table
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS iosapp.user_profiles (
                user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                device_id VARCHAR(255) UNIQUE NOT NULL,
                personal_info JSONB DEFAULT '{}'::jsonb,
                job_preferences JSONB DEFAULT '{}'::jsonb,
                notification_settings JSONB DEFAULT '{}'::jsonb,
                privacy_settings JSONB DEFAULT '{}'::jsonb,
                match_keywords JSONB DEFAULT '[]'::jsonb,
                profile_completeness INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        await db_manager.execute_query(create_table_sql)
        logger.info("✅ user_profiles table created")
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_profiles_device_id ON iosapp.user_profiles (device_id);",
            "CREATE INDEX IF NOT EXISTS idx_user_profiles_match_keywords ON iosapp.user_profiles USING GIN (match_keywords);",
            "CREATE INDEX IF NOT EXISTS idx_user_profiles_created_at ON iosapp.user_profiles (created_at);",
        ]
        
        for index_sql in indexes:
            await db_manager.execute_query(index_sql)
        logger.info("✅ Indexes created")
        
        # Add comments
        comments = [
            "COMMENT ON TABLE iosapp.user_profiles IS 'User profile data with keyword matching support';",
            "COMMENT ON COLUMN iosapp.user_profiles.match_keywords IS 'User-defined keywords for job matching stored as JSONB array';",
        ]
        
        for comment_sql in comments:
            await db_manager.execute_query(comment_sql)
        logger.info("✅ Comments added")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating user_profiles table: {e}")
        return False

async def create_helper_functions():
    """Create helper functions for keyword management"""
    try:
        logger.info("🔧 Creating helper functions...")
        
        # Function to extract keywords
        extract_function = """
            CREATE OR REPLACE FUNCTION iosapp.extract_user_match_keywords(p_device_id VARCHAR)
            RETURNS TEXT[] AS $$
            BEGIN
                RETURN (
                    SELECT ARRAY(
                        SELECT jsonb_array_elements_text(match_keywords)
                        FROM iosapp.user_profiles 
                        WHERE device_id = p_device_id
                    )
                );
            END;
            $$ LANGUAGE plpgsql;
        """
        await db_manager.execute_query(extract_function)
        
        # Function to update keywords
        update_function = """
            CREATE OR REPLACE FUNCTION iosapp.update_user_match_keywords(
                p_device_id VARCHAR,
                p_keywords TEXT[]
            )
            RETURNS BOOLEAN AS $$
            BEGIN
                UPDATE iosapp.user_profiles 
                SET 
                    match_keywords = to_jsonb(p_keywords),
                    last_updated = CURRENT_TIMESTAMP
                WHERE device_id = p_device_id;
                
                RETURN FOUND;
            END;
            $$ LANGUAGE plpgsql;
        """
        await db_manager.execute_query(update_function)
        
        logger.info("✅ Helper functions created")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating helper functions: {e}")
        return False

async def create_sample_profile():
    """Create a sample profile for testing"""
    try:
        logger.info("👤 Creating sample user profile...")
        
        sample_profile_sql = """
            INSERT INTO iosapp.user_profiles (
                device_id, 
                personal_info, 
                job_preferences,
                match_keywords,
                profile_completeness
            ) VALUES (
                'test-device-123',
                '{"firstName": "John", "lastName": "Doe", "email": "john@example.com"}'::jsonb,
                '{"skills": ["Python", "JavaScript"], "desiredJobTypes": ["Full-time"]}'::jsonb,
                '["python", "javascript", "react", "backend"]'::jsonb,
                75
            ) ON CONFLICT (device_id) 
            DO UPDATE SET 
                match_keywords = EXCLUDED.match_keywords,
                last_updated = CURRENT_TIMESTAMP;
        """
        await db_manager.execute_query(sample_profile_sql)
        logger.info("✅ Sample profile created")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating sample profile: {e}")
        return False

async def main():
    """Main function"""
    try:
        logger.info("🚀 Setting up user_profiles with keyword matching...")
        
        # Step 1: Create user_profiles table
        if not await create_user_profiles_table():
            return False
        
        # Step 2: Create helper functions
        if not await create_helper_functions():
            return False
        
        # Step 3: Create sample profile
        if not await create_sample_profile():
            return False
        
        logger.info("🎉 User profiles setup completed successfully!")
        logger.info("✅ Ready for profile-based keyword matching!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())